import configparser
import json
import logging
import os
import re
import shutil
import smtplib
import ssl
import subprocess
import sys
from decimal import localcontext, Decimal, ROUND_HALF_UP, ROUND_HALF_DOWN
from email.message import EmailMessage
from ftplib import FTP, error_perm
from typing import List

import geopandas as gpd
import pandas as pd
from cryptography.fernet import Fernet
from google.cloud import storage
from osgeo import gdal
from sqlalchemy import create_engine, text

import constants as ct

gdal.UseExceptions()
config = configparser.ConfigParser()
config.read(ct.CONFIG_INI)

done_str = f"{'*' * 10} Done {'*' * 10}\n"
logger = logging.getLogger(__name__)


def read_file(file_path):
    with open(file_path, "rb") as rf:
        data = rf.read()
    return data


def write_file(file_path, data):
    with open(file_path, "wb") as wf:
        wf.write(data)


def error_log(err):
    trace = []
    tb = err.__traceback__
    while tb is not None:
        path = os.path.normpath(tb.tb_frame.f_code.co_filename)
        path_last_two_level = "/".join(path.split(os.sep)[-2:])
        trace.append(
            {
                "filename": path_last_two_level,
                "name": tb.tb_frame.f_code.co_name,
                "line": tb.tb_lineno,
            }
        )
        tb = tb.tb_next
    last_trace = trace[-1]
    msg = (
        f"{type(err).__name__}\t{last_trace['filename']}: "
        f"{last_trace['line']}\n\t{str(err)}"
    )
    logger.error(msg)


def error_process(message: str, error):
    """

    Args:
        message: Error message for log
        error: Exception object

    Returns:

    """
    logger.error(message)
    error_log(error)
    # send_email(state, message)
    sys.exit(1)


def get_connection_string(config_db, db_name):
    connect_string = "mysql+pymysql://{}:{}@{}:{}/{}".format(
        config_db["DB_USER"],
        config_db["DB_PASS"],
        config_db["HOST"],
        config_db["PORT"],
        db_name,
    )
    return connect_string


def encrypt_json(input_json, output_path, key):
    # If input_json is bytes, decode it to string first
    if isinstance(input_json, bytes):
        input_json = input_json.decode("utf-8")

    # Now convert to JSON string
    json_str = json.dumps(input_json)

    # Encrypt and save
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(json_str.encode())

    with open(output_path, "wb") as f:
        f.write(encrypted_data)


def decrypt_json(encrypted_data, key):
    """Decrypts a JSON string that was encrypted using Fernet."""
    # Load the key
    fernet = Fernet(key)
    # Decrypt the JSON string
    decrypted_bytes = fernet.decrypt(encrypted_data)
    # Decode the decrypted bytes to a string
    decrypted_string = decrypted_bytes.decode("utf-8")
    # Parse the decrypted string as JSON
    decrypted_json = json.loads(decrypted_string)

    return decrypted_json


def create_directory(directory: str, delete=False) -> str:
    exists = os.path.exists(directory)
    if exists and delete:
        delete_files(directory)
    elif not exists:
        os.makedirs(directory)
    return directory


def delete_files(directory: str) -> None:
    files = os.listdir(directory)
    if len(files) > 0:
        for fname in os.listdir(directory):
            fpath = os.path.join(directory, fname)
            try:
                shutil.rmtree(fpath)
            except OSError:
                os.remove(fpath)


def get_raw_grb_list(directory: str) -> List[str]:
    grb_lst = []
    for f in os.listdir(directory):
        if f.endswith("grb"):
            grb_lst.append(os.path.join(directory, f))
    return grb_lst


def cmd_subprocess(cmd: List[str]) -> None:
    """
    Runs CMD
    Args:
        cmd (List[str]): Commands in list format.
    """
    try:
        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        out, err = proc.communicate()
        rc = proc.returncode
    except Exception as e:
        error_log(e)
    else:
        if rc:
            msg = err.decode("utf-8")
            logger.error(msg)
            logger.error("PROCESS INCOMPLETE")
            sys.exit(1)


def execute_stored_procedure(connection_string, procedure_name, *args):
    """
    Execute a stored procedure using SQLAlchemy

    Args:
        connection_string: Database connection URL
        procedure_name: Name of the stored procedure
        *args: Variable arguments to pass to the stored procedure

    Returns:
        Result of the stored procedure
    """
    try:
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            if args:
                params = ",".join(["%s" for _ in args])
                query = text(f"CALL {procedure_name}({params})")
                result = conn.execute(query, args)
            else:
                query = text(f"CALL {procedure_name}()")
                result = conn.execute(query)

            # Fetch all results if any
            if result:
                column_names = result.keys()
                fetched_data = [
                    dict(zip(column_names, row)) for row in result.fetchall()
                ]
                return fetched_data
        engine.dispose()
        return

    except Exception as e:
        error_log(e)
        raise


def regex_find(regex: str, string: str):
    """
    Perform regex pattern search "findall".
    Args:
        regex (str): Regex pattern
        string (str): Text

    Returns (List[str]): List of matched strings when there are matches, otherwise
    returns None.

    """
    pattern = re.compile(regex)
    match = pattern.findall(string)
    if len(match) > 0:
        return match


def list_grbs_not_today(file_dir: str) -> List[str]:
    """
    Finds dated GRB and other than GRB files.
    Args:
        file_dir (srt): File directory
    """
    files = []
    for f in os.listdir(file_dir):
        if f.endswith("grb"):
            match = regex_find(ct.REG_PATTERN_TODAY, f)
            if match is None:  # GRB not today's data
                files.append(f)
        else:  # File not GRB
            files.append(f)
    return files


def delete_outdated_grbs(file_dir: str) -> None:
    """
    Deletes outdated GRB and other than GRB files.
    Args:
        file_dir (str): Directory for raw GRB files.
    """
    logger.info("[Delete GRB files other than today's data]")
    files = list_grbs_not_today(file_dir)
    if len(files) > 0:
        for f in files:
            fpath = os.path.join(file_dir, f)
            if os.path.isdir(fpath):
                shutil.rmtree(fpath)
                logger.info(f"{f} directory deleted.")
            elif os.path.isfile(fpath):
                os.remove(fpath)
                logger.info(f"{f} deleted.")
    else:
        logger.info(f"No data to delete.")
    logger.info(done_str)


def list_files(f_dir, ext):
    files = [os.path.join(f_dir, f) for f in os.listdir(f_dir) if f.endswith(ext)]
    return files


def send_email(message, state=None):
    try:
        notif = config["Notification"]
        em = EmailMessage()
        em["From"] = notif["EMAIL_SENDER"]
        em["To"] = notif["EMAIL_RECEIVER"]
        if state:
            em["Subject"] = f"{state} {notif['EMAIL_SUBJECT']}"
        else:
            em["Subject"] = f"{notif['EMAIL_SUBJECT']}"

        em.set_content(message)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(notif["EMAIL_SENDER"], notif["GMAIL_API_CREDENTIAL"])
            smtp.sendmail(
                notif["EMAIL_SENDER"], notif["EMAIL_RECEIVER"], em.as_string()
            )
    except Exception as e:
        error_log(e)
        exit(1)


def calculate_duration(start, stop):
    elapsed = stop - start
    logger.info(f"Start:\t{start}")
    logger.info(f"End:\t\t{stop}")
    logger.info(f"Duration: {elapsed}")


def run_gdal_to_tiff(in_fpath, out_fpath, band, tsrs=None):
    try:
        in_fname = os.path.basename(in_fpath).split(".")[0]

        if tsrs:
            warp_options = gdal.WarpOptions(format="GTiff", srcBands=band, dstSRS=tsrs)
        else:
            warp_options = gdal.WarpOptions(format="GTiff", srcBands=band)

        with gdal.Open(in_fpath) as input_obj:
            gdal.Warp(out_fpath, input_obj, options=warp_options)
            logger.info(f"{in_fname} --- converted")
    except Exception as e:
        error_log(e)


def run_gdal_resample(in_fpath, out_fpath, xres, yres, nodata):
    try:
        in_fname = os.path.basename(in_fpath)
        out_fname = os.path.basename(out_fpath)
        warp_options = gdal.WarpOptions(
            xRes=xres, yRes=yres, resampleAlg="bilinear", dstNodata=nodata
        )
        with gdal.Open(in_fpath) as input_obj:
            gdal.Warp(out_fpath, input_obj, options=warp_options)
            logger.info(f"{in_fname} to {out_fname} ---> completed")
    except Exception as e:
        error_log(e)


def round_half_up(num):
    with localcontext() as ctx:
        ctx.rounding = ROUND_HALF_UP
        n = Decimal(num)
        return n.to_integral_value()


def round_half_down(num):
    with localcontext() as ctx:
        ctx.rounding = ROUND_HALF_DOWN
        n = Decimal(num)
        return n.to_integral_value()


def download_grbs(grb_raw_dir, files, ftp_url, ftp_cwd) -> None:
    """
    Download PQPF GRB files from FTP.
    Args:
        grb_raw_dir (str): Path to GRIB raw files
        files (List[str]): List of GRB files
        ftp_url (str): FTP URL
        ftp_cwd (str): FTP current working directory
    """
    logger.info("[Download GRIBs from FTP]")
    try:
        if files:
            ftp = FTP(ftp_url)
            ftp.login()
            ftp.encoding = "utf-8"
            ftp.cwd(ftp_cwd)
            for fname in files:
                grb_path = os.path.join(grb_raw_dir, fname)
                try:
                    with open(grb_path, "wb") as f:
                        ftp.retrbinary("RETR " + fname, f.write)
                    logger.info(f"{fname} downloaded.")

                except error_perm:
                    print("ERR", fname)
                    os.unlink(grb_path)
            ftp.quit()
        else:
            logger.info("Skip download")
        logger.info(done_str)
    except Exception as e:
        msg = "GRB file download failed."
        error_process(msg, e)


def get_thresholds(lease_shp, thresholds_col_name):
    """
    Get unique rain threshold (inches) values.

    Args
        lease_shp (str): The lease shp name
        thresholds_col_name (str): Threshold column name
    Returns (List[float]): A list of unique rainfall thresholds
    """
    logger.info("[Get unique rainfall thresholds]")
    try:
        gdf = gpd.read_file(lease_shp)
        thresholds = sorted(
            gdf[thresholds_col_name].unique()
        )  # Returns list of class numpy.float64
        if len(thresholds) > 0:
            thresholds_num = [float(threshold) for threshold in thresholds]
            thresholds_str = ", ".join([str(threshold) for threshold in thresholds])
            logger.info(f"Thresholds: {thresholds_str}")
            logger.info(done_str)
            return thresholds_num
        else:
            raise
    except Exception as e:
        msg = "Failed to get rainfall thresholds."
        error_process(msg, e)


def set_conditions_list(values):
    return [values >= 0.9, values >= 0.75, values >= 0.5, values >= 0.25, values < 0.25]


def db_connection_test(connect_str):
    logger.info("[DB connection test]")
    try:
        engine = create_engine(connect_str)
        conn = engine.connect()
        # tables = conn.execute('SHOW TABLES;')
        # print(tables.all())
        conn.close()
        engine.dispose()
        logger.info(f"{'*' * 10} Connected {'*' * 10}\n")
    except Exception as e:
        msg = "DB connection failed."
        error_process(msg, e)


def save_to_db(connect_str, csv_path) -> None:
    """
    Saves the data to DB.
    Args:
        connect_str (str): DB connection string
        csv_path (str): CMU probabilities CSV file path
    """
    logger.info("[Save to DB]")
    try:
        engine = create_engine(connect_str)
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path, index_col=False)
            if len(df.index) > 0:
                with engine.begin() as conn:
                    conn.execute(text("CALL DeleteCmuProbsToday()"))
                    df.to_sql(
                        "cmu_probabilities", con=conn, if_exists="append", index=False
                    )
                    queryset = conn.execute(text("CALL SelectCmuProbsToday()"))
                    if queryset.rowcount == len(df.index):
                        logger.info(f"{queryset.rowcount} rows added to DB.")
        logger.info(done_str)
    except Exception as e:
        msg = "Save to DB failed."
        error_process(msg, e)


def convert_date_string(date_str):
    """
    Convert a date range string (e.g., "11/1-2/28") to datetime objects with correct
    years based on date today.

    Args:
        date_str: String in format "MM/DD-MM/DD"

    Returns:
        dict: Dictionary with 'start' and 'end' datetime objects
    """
    from datetime import datetime

    today = datetime.today()
    date_lst = date_str.split("-")
    dates = {"start": None, "end": None}
    
    if len(date_lst) == 2:
        start_str, end_str = date_lst
        start_month, start_day = map(int, start_str.split("/"))
        end_month, end_day = map(int, end_str.split("/"))

        # Determine years based on a month sequence
        if end_month < start_month:  # Date range crosses year boundary
            if today.month >= start_month:
                years = (today.year, today.year + 1)
            elif today.month <= end_month:
                years = (today.year - 1, today.year)
            else:
                years = (today.year, today.year + 1)
        else:
            years = (today.year, today.year)

        # Create datetime objects
        dates["start"] = datetime(years[0], start_month, start_day)
        dates["end"] = datetime(years[1], end_month, end_day)
    
    return dates


def is_season(date_today, start, end):
    # Convert datetime objects to date objects for comparison
    if hasattr(date_today, "date"):
        date_today = date_today.date()
    if hasattr(start, "date"):
        start = start.date()
    if hasattr(end, "date"):
        end = end.date()

    if start <= date_today <= end:
        return True
    else:
        return False


def download_files_from_gcloud_bucket(bucket_name, local_dir):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blobs = bucket.list_blobs()
    for blob in blobs:
        if not blob.name.endswith("/"):
            local_path = os.path.join(local_dir, blob.name.split("/")[-1])
            blob.download_to_filename(filename=str(local_path))
