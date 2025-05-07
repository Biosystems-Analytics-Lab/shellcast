"""
Configuration and directory management for PQPF data processing.
Uses properties for better encapsulation and control over directory paths.
"""

import configparser
import os
import platform
from datetime import datetime
import pytz

import utils
from constants import CONFIG_INI, ROOT_DIR, PQPF_DATA_DIR, TP_DATA_DIR


class DirectoryConfig:
    def __init__(self, state: str, db: str):
        """
        Initialize configuration and directory management.

        Args:
            state (str): State abbreviation
            db (str): Database configuration section name
        """
        self._state = state.upper()
        self._db = db
        self._config = configparser.ConfigParser()
        self._config.read(CONFIG_INI)
        self._date_today = datetime.now(pytz.timezone("America/New_York")).date()
        self._data_root = os.path.join(PQPF_DATA_DIR, self._state.lower())

    @property
    def os_type(self) -> str:
        """Operating system type."""
        return "Other" if platform.system() == "Darwin" else "Windows"

    @property
    def state(self) -> str:
        """State abbreviation in uppercase."""
        return self._state

    @property
    def date_today(self) -> datetime.date:
        """Today's date in America/New_York timezone."""
        return self._date_today

    @property
    def config(self) -> configparser.ConfigParser:
        """Configuration parser instance."""
        return self._config

    @property
    def data_root(self) -> str:
        """Root directory for state-specific data."""
        return self._data_root

    @property
    def connect_str(self) -> str:
        """Database connection string."""
        return utils.get_connection_string(
            self._config[self._db], self._config[self._state]["DB_NAME"]
        )

    @property
    def inputs_dir(self) -> str:
        """Directory for input files."""
        return os.path.join(self._data_root, "inputs")

    @property
    def outputs_dir(self) -> str:
        """Directory for output files."""
        return utils.create_directory(
            os.path.join(self._data_root, "outputs"), delete=True
        )

    @property
    def grb_raw_dir(self) -> str:
        """Directory for raw GRIB files."""
        return utils.create_directory(os.path.join(PQPF_DATA_DIR, "raw"))

    @property
    def intermediate_dir(self) -> str:
        """Directory for intermediate processing files."""
        return utils.create_directory(
            os.path.join(self._data_root, "intermediate"), delete=True
        )

    @property
    def grb_subsets_dir(self) -> str:
        """Directory for subset GRIB files."""
        return utils.create_directory(
            os.path.join(self._data_root, "intermediate", "subsets"), delete=True
        )

    @property
    def tiffs_dir(self) -> str:
        """Directory for TIFF files."""
        return utils.create_directory(
            os.path.join(self._data_root, "intermediate", "tiffs"), delete=True
        )

    @property
    def lease_shp(self) -> str:
        """Path to lease shapefile."""
        return os.path.join(
            self._data_root, "inputs", self._config[self._state]["LEASE_SHP"]
        )

    @property
    def bucket_name(self) -> str:
        """GCP bucket name."""
        return self._config["gcp.bucket"]["BUCKET_NAME"]

    @property
    def tp_intermediate_dir(self) -> str:
        """Directory for total precipitation intermediate processing files."""
        return utils.create_directory(
            os.path.join(TP_DATA_DIR, "intermediate"), delete=True
        )


class NotificationConfig:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(CONFIG_INI)

    @property
    def gmail_api_credential_file(self):
        return ROOT_DIR / self.config["Notification"]["GMAIL_API_CREDENTIAL_FILE"]

    @property
    def token_file(self):
        return ROOT_DIR / self.config["Notification"]["GMAIL_API_TOKEN_FILE"]

    @property
    def stored_procedure(self):
        return self.config["Notification"]["DB_STORED_PROCEDURE"]

    @property
    def scopes(self):
        return ["https://www.googleapis.com/auth/gmail.send"]

    @property
    def encryption_key_env(self):
        return "SHELLCAST_TOKEN_KEY"

    @property
    def sender(self):
        return self.config["Notification"]["EMAIL_SENDER"]

    @property
    def subject_template(self):
        return "{} ShellCast Forecasts for {}"

    @property
    def charset(self):
        return "UTF-8"

    @property
    def notification_header(self):
        return "https://go.ncsu.edu/shellcast\n\n"

    @property
    def lease_template(self):
        return (
            "One or more of your leases is at risk of closing today, tomorrow or in 2 days.\n"
            "Visit https://go.ncsu.edu/shellcast for details."
        )
    
    @property
    def lease_template_today_only(self):
        return (
            "One or more of your leases is at risk of closing today\n"
            "Visit https://go.ncsu.edu/shellcast for details."
        )

    @property
    def notification_footer(self):
        return (
            "\nThese predictions are in no way indicative of whether or not a lease will actually be "
            "temporarily closed for harvest."
        )

    @property
    def dev_email_receivers(self):
        return self.config["FL.Developer"]["EMAIL_RECEIVER"]

    @property
    def dev_send_email(self):
        return self.config["FL.Developer"]["SEND_EMAIL_TO_DEVELOPER"]
