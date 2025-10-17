import logging.config
import os
from pathlib import Path

import yaml

LOGS_DIR = str(Path(Path().absolute().parent, "logs"))


def set_logging_config(state):
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
        },
        "handlers": {
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "standard",
            },
            "info_file_handler": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "standard",
                "filename": os.path.join(LOGS_DIR, state.lower(), "info.log"),
                "maxBytes": 10485760,
                "backupCount": 20,
                "encoding": "utf8",
            },
            "error_file_handler": {
                "level": "ERROR",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "standard",
                "filename": os.path.join(LOGS_DIR, state.lower(), "error.log"),
                "maxBytes": 10485760,
                "backupCount": 20,
                "encoding": "utf8",
            },
        },
        "loggers": {
            "": {
                "handlers": ["console", "info_file_handler", "error_file_handler"],
                "level": "INFO",
                "propagate": True,
            }
        },
    }

    return logging_config


def create_log_files(state):
    log_dir = os.path.join(LOGS_DIR, state.lower())
    info_log_fpath = os.path.join(log_dir, "info.log")
    error_log_fpath = os.path.join(log_dir, "error.log")
    log_files = [info_log_fpath, error_log_fpath]
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    for log_file in log_files:
        if not os.path.exists(log_file):
            log_file = open(log_file, "w")
            log_file.close()


def setup_logger(state):
    logging_config = set_logging_config(state)
    logging.config.dictConfig(logging_config)
    logging.captureWarnings(True)


def setup_logger_yaml(logging_yaml_fpath):
    with open(logging_yaml_fpath, "r") as stream:
        config = yaml.load(stream, Loader=yaml.FullLoader)

    logging.config.dictConfig(config)
    logging.captureWarnings(True)
