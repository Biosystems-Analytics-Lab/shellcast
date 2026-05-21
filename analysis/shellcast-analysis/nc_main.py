"""
Project: ShellCast North Carolina
Date: November 2022 - 2023
"""

import sys
from pathlib import Path

shellcast_analysis_dir = str(Path().absolute().parents[1])
script_dir = str(Path(Path().absolute(), "src"))
sys.path.append(script_dir)

import setup_logging  # noqa: E402

STATE = "NC"

setup_logging.create_log_files(STATE)
setup_logging.setup_logger(STATE)

import logging  # noqa: E402

from management import DirectoryConfig, NotificationConfig  # noqa: E402
from nc_pqpf.nc_pqpf import NCPQPF  # noqa: E402
from notifications import EmailNotification  # noqa: E402

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info(f"{'=' * 50}")
    logger.info("\tStart NC ShellCast Analysis")
    logger.info(f"{'=' * 50}")
    # DB connection information in analysis_settings.ini
    db = "gcp.mysql"

    # --- Directory configurations ---
    dir_config = DirectoryConfig(STATE, db)

    # --- PQPF analysis ---
    pqpf = NCPQPF(dir_config)
    pqpf.main()

    # --- Email notification ---
    notification_config = NotificationConfig(STATE)
    if notification_config.notifications_enabled:
        try:
            email_notify_inst = EmailNotification(
                dir_config, notification_config, STATE
            )
            email_notify_inst.send()
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
    else:
        logger.info(f"Notifications are disabled for {STATE} in configuration")

    # ---------------------
    logger.info(f"{'=' * 50}")
