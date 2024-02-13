"""
Project: ShellCast North Carolina
Date: November 2022 - 2023
"""
import sys
import os
import subprocess
from pathlib import Path

# script_dir = os.path.join(os.path.dirname(__file__), '..', '..')
shellcast_analysis_dir = str(Path().absolute().parents[1])
script_dir = str(Path(Path().absolute(), 'src'))
sys.path.append(script_dir)

import setup_logging

STATE = 'FL'

setup_logging.create_log_files(STATE)
setup_logging.setup_logger_yaml(os.path.join(os.path.dirname(__file__), 'fl_logging.yaml'))
# setup_logging.setup_logger_yaml(yaml_fpath)

from fl_pqpf.tp_xmrg import TPXMRG
from fl_pqpf.fl_pqpf import FLPQPF
import logging

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info(f'{"=" * 50}')
    logger.info('\t\t\t  Start FL ShellCast Analysis')
    logger.info(f'{"=" * 50}')
    # DB connection information in config.ini
    db = 'gcp.mysql'

    # --- Download and process total precipitation XMRG dataset ---
    tpxmrg = TPXMRG('FL', 7)
    tpxmrg.main()

    # --- PQPF analysis ---
    pqpf = FLPQPF(db)
    pqpf.main()

    # ---------------------
    logger.info(f'{"=" * 50}')
