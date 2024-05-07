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

STATE = 'FL'

setup_logging.create_log_files(STATE)
setup_logging.setup_logger(STATE)

from fl_pqpf.tp_xmrg import TPXMRG  # noqa: E402
from fl_pqpf.fl_pqpf import FLPQPF  # noqa: E402
import logging  # noqa: E402

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info(f'{"=" * 50}')
    logger.info('\t\t\t  Start FL ShellCast Analysis')
    logger.info(f'{"=" * 50}')
    # DB connection information in config.ini
    db = 'gcp.mysql'

    # --- Download and process total precipitation XMRG dataset ---
    tpxmrg = TPXMRG('FL', 14)
    tpxmrg.main()

    # --- PQPF analysis ---
    pqpf = FLPQPF(db, save=False)
    pqpf.main()

    # ---------------------
    logger.info(f'{"=" * 50}')
