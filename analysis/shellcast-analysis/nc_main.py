"""
Project: ShellCast North Carolina
Date: November 2022 - 2023
"""
import sys
from pathlib import Path


shellcast_analysis_dir = str(Path().absolute().parents[1])
script_dir = str(Path(Path().absolute(), 'src'))
sys.path.append(script_dir)

import setup_logging  # noqa: E402

STATE = 'NC'

setup_logging.create_log_files(STATE)
setup_logging.setup_logger(STATE)

from nc_pqpf.nc_pqpf import NCPQPF  # noqa: E402
import logging  # noqa: E402

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info(f'{"="*50}')
    logger.info('\tStart NC ShellCast Analysis')
    logger.info(f'{"="*50}')
    # DB connection information in config.ini
    db = 'gcp.mysql'

    # --- PQPF analysis ---
    pqpf = NCPQPF(db, save=True)
    pqpf.main()

    # ---------------------
    logger.info(f'{"=" * 50}')
