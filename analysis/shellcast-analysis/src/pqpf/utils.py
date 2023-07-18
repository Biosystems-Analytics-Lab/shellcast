import os
import sys
import subprocess
import smtplib
import ssl
import codecs
import shutil
import re
import logging
import configparser
from typing import List
from email.message import EmailMessage
import constants as ct

config = configparser.ConfigParser()
config.read(ct.CONFIG_INI)

done_str = f'{"*"*10} Done {"*"*10}\n'
logger = logging.getLogger(__name__)


def error_log(err):
    trace = []
    tb = err.__traceback__
    while tb is not None:
        path = os.path.normpath(tb.tb_frame.f_code.co_filename)
        path_last_two_level = '/'.join(path.split(os.sep)[-2:])
        trace.append({
            "filename": path_last_two_level,
            "name": tb.tb_frame.f_code.co_name,
            "line": tb.tb_lineno
        })
        tb = tb.tb_next
    last_trace = trace[-1]
    msg = f'{type(err).__name__}\t{last_trace["filename"]}:{last_trace["line"]}\n\t{str(err)}'
    logger.error(msg)


def error_process(state, message, error):
    logger.error(message)
    error_log(error)
    send_email(state, message)
    sys.exit(1)


def get_connection_string(config_db, db_name):
    connect_string = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(
        config_db['DB_USER'],
        config_db['DB_PASS'],
        config_db['HOST'],
        config_db['PORT'],
        db_name)
    return connect_string


def create_directory(directory: str, delete=False) -> str:
    exists = os.path.exists(directory)
    if exists:
        if delete:
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


def cmd_subprocess(cmd: List[str]) -> None:
    """
    Runs CMD
    Args:
        cmd (List[str]): Commands in list format.
    """
    try:
        proc = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        out, err = proc.communicate()
        # logger.info(codecs.decode(out, 'UTF-8'))
        rc = proc.returncode
    except Exception as e:
        error_log(logger, e)
    else:
        if rc:
            error_log(logger, err)
            logger.error(codecs.decode(err, 'UTF-8'))
            logger.error('PROCESS INCOMPLETE')
            sys.exit(1)


def regex_find(regex: str, text: str) -> List[str]:
    """
    Perform regex pattern search "findall".
    Args:
        regex (str): Regex pattern
        text (str): Text

    Returns (List[str}): List of matched strings when there are matches, otherwise returns None.

    """
    pattern = re.compile(regex)
    match = pattern.findall(text)
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
        if f.endswith('grb'):
            match = regex_find(ct.REG_PATTERN_TODAY, f)
            if match is None:  # GRB not today's data
                files.append(f)
        else:  # File not GRB
            files.append(f)
    return files


def delete_grbs(file_dir: str) -> None:
    """
    Deletes outdated GRB and other than GRB files.
    Args:
        file_dir (str): Directory for raw GRB files.
    """
    logger.info('[Delete GRB files other than today\'s data]')
    files = list_grbs_not_today(file_dir)
    if len(files) > 0:
        for f in files:
            fpath = os.path.join(file_dir, f)
            if os.path.isdir(fpath):
                shutil.rmtree(fpath)
                logger.info(f'{f} directory deleted.')
            elif os.path.isfile(fpath):
                os.remove(fpath)
                logger.info(f'{f} deleted.')
    else:
        logger.info(f'No data to delete.')
    logger.info(done_str)


def list_files(f_dir, ext):
    files = [os.path.join(f_dir, f) for f in os.listdir(f_dir) if f.endswith(ext)]
    return files


def send_email(state, message):
    try:
        notif = config['Notification']
        em = EmailMessage()
        em['From'] = notif['EMAIL_SENDER']
        em['To'] = notif['EMAIL_RECEIVER']
        em['Subject'] = f'{state} {notif["EMAIL_SUBJECT"]}'
        em.set_content(message)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(notif['EMAIL_SENDER'], notif['GMAIL_API_CREDENTIAL'])
            smtp.sendmail(notif['EMAIL_SENDER'], notif['EMAIL_RECEIVER'], em.as_string())
    except Exception as e:
        error_log(logger, e)
        exit(1)


def calculate_duration(start, stop):
    elapsed = stop - start
    logger.info(f'Start:\t{start}')
    logger.info(f'End:\t\t{stop}')
    logger.info(f'Duration: {elapsed}')

