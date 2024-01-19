"""
Setting PQPF folders
"""
import configparser
import os
import logging.config
import warnings
import platform
import constants as ct
from shapely.errors import ShapelyDeprecationWarning
from datetime import datetime
from pqpf import utils

warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)

logger = logging.getLogger(__name__)


class ProcDirs:
    def __init__(self, state, db):
        """
        Args:
            state (str): State abbreviation
            db (str):
        """
        self.os_type = 'Other' if platform.system() == 'Darwin' else 'Windows'

        self.outfile_date = datetime.today().strftime('%Y-%m-%d')
        self.config = configparser.ConfigParser()
        self.config.read(ct.CONFIG_INI)
        self.state = state.upper()
        self.data_root = os.path.join(ct.PQPF_DATA_DIR, state.lower())
        self.connect_str = utils.get_connection_string(self.config[db], self.config[self.state]['DB_NAME'])
        # Data directories
        self.inputs_dir = os.path.join(self.data_root, 'inputs')
        self.outputs_dir = utils.create_directory(os.path.join(self.data_root, 'outputs'), delete=True)
        self.grb_raw_dir = utils.create_directory(os.path.join(ct.PQPF_DATA_DIR, 'raw'))
        self.intermediate_dir = utils.create_directory(os.path.join(self.data_root, 'intermediate'),
                                                               delete=True)
        self.grb_subsets_dir = utils.create_directory(os.path.join(self.intermediate_dir, 'subsets'),
                                                      delete=True)
        self.tiffs_dir = utils.create_directory(os.path.join(self.intermediate_dir, 'tiffs'), delete=True)

        self.lease_shp = os.path.join(self.inputs_dir, self.config[self.state]['LEASE_SHP'])
