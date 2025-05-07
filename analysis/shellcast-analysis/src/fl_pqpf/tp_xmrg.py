"""

Notes: Florida's maximum accumulation of total precipitation is 7 days. The ShellCast forecasts the total precipitation
for today. The forecast today and 6 days of past data make up a total of 7 days. Due to PQPF data availability,
ShellCast defines a day as the period between 7 am and 24 hours prior.
"""

import gzip
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from ftplib import FTP, error_perm
from pathlib import Path
from typing import List

import pytz

import constants as ct
import utils

logger = logging.getLogger(__name__)


def divide_chunks(lst, n):
    # looping till length l
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def reverse(lst):
    new_lst = lst[::-1]
    return new_lst


def add_gz_to_filename(download_file_lst):
    result = []
    if len(download_file_lst) > 0:
        for f in download_file_lst:
            result.append(f"{f}.gz")
        return result


class MissingTPGRBsError(Exception):
    """Raw XMRG Total Precipitation file directory must contain 120 (5 days), 144 (6 days), or 163 (7days) files."""

    pass


class TPXMRG:
    def __init__(self, state, hour_from):
        """
        Download the XMRG GRIB files for the past 120 hours (5 days) from NOAA's FTP site. Upon downloading 120 XMRG
        GRIB files, run the [xmrg_proc.sh] command to process them.

        Args:
            state (str): Abbreviated state name in upper case.
            hour_from (int): Hours in 24 hours format. 7:00 AM should be the setting for ShelCast. In this case, input
            is 7. Due to limited availability of data in the afternoon for 7 AM data, you might need to adjust your
            development environment time.
        """
        self.state = state.upper()
        self.tp_proc_sh = os.path.join(os.path.dirname(__file__), "xmrg_proc.sh")
        self.tp_raw_dir = os.path.join(ct.TP_DATA_DIR, "raw")
        utils.create_directory(self.tp_raw_dir)
        self.hour_from = hour_from
        self.max_threshold_days = 6

    def list_required_tp_data(self) -> List[str]:
        """
        List required total precipitation files.
        Args:
            days (int): Days past from today
        Returns:
            file_names: A list of hourly total precipitation date and time.
        """
        try:
            today = datetime.now(pytz.timezone("America/New_York")).today()
            days_in_hours = self.max_threshold_days * 24
            file_names = []
            new_datetime = today.replace(hour=self.hour_from, minute=0, second=0)

            while days_in_hours > 0:
                past = new_datetime - timedelta(hours=days_in_hours)
                dt_format = past.strftime("%m%d%Y%H")
                fname = f"xmrg{dt_format}z.grb"
                file_names.append(fname)
                days_in_hours -= 1

            return file_names

        except Exception as e:
            logger.error(e)
            sys.exit(1)

    def list_existing_tp_data(self) -> List[str]:
        """
        List names of existing XMRG files.

        Returns:
            exist_files: A list of existing XMRG files.
        """
        exist_files = [f.name for f in Path(self.tp_raw_dir).glob("xmrg*.grb")]
        return exist_files

    def ungz(self, gz_fpath):
        unzipped = str(gz_fpath).split(".gz")[0]
        with gzip.open(gz_fpath, "rb") as rf:
            with open(unzipped, "wb") as wf:
                shutil.copyfileobj(rf, wf)
                os.remove(gz_fpath)

    def tp_data_inventory(self, required_files, existing_files):
        """
        Catalog total precipitation data.
        Args:
            required_files (list[str]): Required total precipitation file names (e.g. "xmrg0114202413z.grb")
            existing_files (list[str]): Total precipitation data already in tp/raw folder.

        Returns (list[dict]):
         {'
            day': <int: 1 through 7 - Florida rain threshold days>,
            values: <list(dict)>: [
                {'tpxmrg_name': <str: name of grb file>,
                'path': <str: path for compressed gz file>,
                'exists': <bool: True when file is in tp/raw folder, otherwise False>}, ...] (length of the list should
                be 24),
            'check': <bool: True for required data for "day" is in tp/raw folder, otherwise False.>,
        """

        reversed_lst = reverse(required_files)
        chunk_lst = divide_chunks(reversed_lst, 24)
        inventory = []

        for idx, vals in enumerate(chunk_lst):
            dt_dict = {"day": idx + 1, "values": [], "check": None}
            for val in vals:
                data = {
                    "tpxmrg_name": val,
                    "path": os.path.join(self.tp_raw_dir, val + ".gz"),
                    "exists": False,
                }
                if val in existing_files:
                    data["exists"] = True
                dt_dict["values"].append(data)
            inventory.append(dt_dict)
        return inventory

    def download_tp_data(self, data_inventory, ftp_url, ftp_cwd):
        """
        Download total precipitation data that is not in tp/raw directory. Successful file download, updates
        data_inventory['values']['exists'] to True.
        Args:
            data_inventory (list[dict]): Data catalog created in :func:`.tp_data_inventory`.
            ftp_url (str): NOAA total precipitation FTP URL root
            ftp_cwd (str): NOAA total precipitation FTP subdirectory

        Returns (list[dict]): Updated data_inventory.

        """
        logger.info("[Download GRIBs from FTP]")

        try:
            if data_inventory:
                ftp = FTP(ftp_url)
                ftp.login()
                ftp.encoding = "utf-8"
                ftp.cwd(ftp_cwd)
                for item in data_inventory:
                    if item["day"] < 6:
                        for ele in item["values"]:
                            if not ele["exists"]:
                                try:
                                    with open(ele["path"], "wb") as f:
                                        ftp.retrbinary(
                                            "RETR " + ele["tpxmrg_name"] + ".gz",
                                            f.write,
                                        )
                                    self.ungz(ele["path"])
                                    grb_fpath = ele["path"].split(".gz")[0]
                                    file_size = os.path.getsize(grb_fpath)
                                    if file_size > 0:
                                        ele["exists"] = True
                                        logger.info(f"{ele['tpxmrg_name']} downloaded.")
                                    else:
                                        os.remove(ele["path"])
                                        logger.info(
                                            f"{ele['tpxmrg_name']} file size 0 -> file deleted."
                                        )

                                except error_perm:
                                    logger.error(
                                        f"Download failed -> {item['day']}: {ele['tpxmrg_name']}"
                                    )
                                    os.unlink(ele["path"])
                ftp.quit()
            else:
                logger.info("Skip download")
            logger.info(utils.done_str)

            return data_inventory

        except Exception as e:
            msg = "TP GRB file download failed."
            utils.error_process(msg, e)

    @staticmethod
    def check_tp_data(data_inventory):
        """
        Verify that the precipitation data for a given day exist in the tp/raw directory and record them in the JSON
        file.

        Args:
            data_inventory list(dict):

        Returns:

        """
        for item in data_inventory:
            for ele in item["values"]:
                if ele["exists"]:
                    item["check"] = True
                else:
                    item["check"] = False
                    break
        with open(ct.TP_DATA_CATALOG_PATH, "w") as f:
            json.dump(data_inventory, f)

        return data_inventory

    def delete_tp_data(self, data_inventory):
        """
        Deletes unnecessary total precipitation data from tp/raw directory.

        Args:
            data_inventory (list[dict]): Data inventory data after :func: `.check_tp_data`

        Returns:

        """
        existing_files = self.list_existing_tp_data()
        required_files = []
        for item in data_inventory:
            for ele in item["values"]:
                required_files.append(ele["tpxmrg_name"])
        delete_files = list(set(existing_files).symmetric_difference(required_files))

        for f in delete_files:
            path = os.path.join(self.tp_raw_dir, f)
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

    def days_to_process_tp_data(self, data_inventory):
        """

        Args:
            data_inventory (list[dict]):

        Returns:

        """
        xth_day = None
        for item in data_inventory:
            for num in range(1, self.max_threshold_days + 1):
                if item["day"] == num and not item["check"]:
                    xth_day = num
                    break
            else:
                continue
            break

        if xth_day is None:
            return self.max_threshold_days * 24
        elif xth_day == self.max_threshold_days:
            return (self.max_threshold_days - 1) * 24
        elif xth_day in [1, 2, 3, 4, 5]:
            return 0

    def main(self):
        try:
            xmrg_files = self.list_required_tp_data()
            existing_xmrg_files = self.list_existing_tp_data()
            inventory = self.tp_data_inventory(xmrg_files, existing_xmrg_files)

            af_inventory = self.download_tp_data(
                inventory, ct.TG_FTP_URL, ct.TG_FTP_CWD
            )
            checked_inventory = self.check_tp_data(af_inventory)

            self.delete_tp_data(checked_inventory)

            hours = self.days_to_process_tp_data(checked_inventory)

            if hours > 0:
                subprocess.call(self.tp_proc_sh, shell=True)
            else:
                raise MissingTPGRBsError

        except Exception as e:
            msg = "XMRG processing failed."
            utils.error_process(msg, e)


if __name__ == "__main__":
    tpxmrg = TPXMRG("FL", 7)
    tpxmrg.main()
