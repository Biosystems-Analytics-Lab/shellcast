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

from fl_pqpf.fl_pqpf import FLPQPF  # noqa: E402
from fl_pqpf.tp_xmrg import TPXMRG  # noqa: E402
from management import DirectoryConfig, NotificationConfig  # noqa: E402
from notifications import EmailNotification, DevEmailNotificationFL  # noqa: E402
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
    dir_config = DirectoryConfig(STATE, db)

    # --- PQPF analysis ---
    pqpf = FLPQPF(dir_config, save=True)
    pqpf.main()

    # --- Email notification ---
    notification_config = NotificationConfig()
    email_notify_inst = EmailNotification(
        dir_config, notification_config, STATE, prob_only_today=True
    )
    email_notify_inst.send()

    # --- Developer Email ---
    dev_email_notify_inst = DevEmailNotificationFL(dir_config, notification_config)
    dev_email_notify_inst.send()

    # ---------------------
    logger.info(f"{'=' * 50}")
