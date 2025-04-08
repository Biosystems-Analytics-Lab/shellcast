"""
Project: ShellCast Florida
Date: November 2023-2024
"""

import sys
from pathlib import Path

shellcast_analysis_dir = str(Path(__file__).resolve().parent)
script_dir = str(Path(Path(shellcast_analysis_dir), "src"))
sys.path.append(script_dir)

import setup_logging  # noqa: E402

STATE = "FL"

setup_logging.create_log_files(STATE)
setup_logging.setup_logger(STATE)

from fl_pqpf.tp_xmrg import TPXMRG  # noqa: E402
from fl_pqpf.fl_pqpf import FLPQPF  # noqa: E402
from management import ConfigDirs, NotificationConfig  # noqa: E402
from notifications import EmailNotification, DevEmailNotificationFL
import logging  # noqa: E402

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info(f"{'=' * 50}")
    logger.info("\tStart FL ShellCast Analysis")
    logger.info(f"{'=' * 50}")
    # DB connection information in config.ini
    db = "gcp.mysql"

    # --- Download and process total precipitation XMRG dataset ---
    tpxmrg = TPXMRG(STATE, 7)
    tpxmrg.main()

    # --- Directory configurations ---
    config_dirs = ConfigDirs(STATE, db)

    # --- PQPF analysis ---
    pqpf = FLPQPF(config_dirs, save=True)
    pqpf.main()

    # --- Email notification ---
    config_notification = NotificationConfig()
    email_notify_inst = EmailNotification(config_notification, STATE)
    email_notify_inst.send()

    # --- Developer Email ---
    dev_email_notify_inst = DevEmailNotificationFL(config_dirs, config_notification)
    dev_email_notify_inst.send()

    # ---------------------
    logger.info(f"{'=' * 50}")
