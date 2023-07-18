import logging.config
import os
import yaml

LOGS_DIR = os.path.join(os.path.dirname(__file__), 'logs')

def create_log_files(state):
    log_dir = os.path.join(LOGS_DIR, state.lower())
    info_log_fpath = os.path.join(log_dir, 'info.log')
    error_log_fpath = os.path.join(log_dir, 'error.log')
    log_files = [info_log_fpath, error_log_fpath]
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    for log_file in log_files:
        if not os.path.exists(log_file):
            log_file = open(info_log_fpath, 'w')
            log_file.close()

def setup_logger_yaml(logging_yaml_fpath):
    with open(logging_yaml_fpath, 'r') as stream:
        config = yaml.load(stream, Loader=yaml.FullLoader)

    logging.config.dictConfig(config)
    logging.captureWarnings(True)
