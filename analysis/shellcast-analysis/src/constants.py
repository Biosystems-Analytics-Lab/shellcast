import os
from datetime import datetime
from pathlib import Path

# [ Directories ]
ROOT_DIR = Path(__file__).resolve().parent.parent
PREPROC_DATA_DIR = os.path.join(ROOT_DIR, 'data/preprocs')
PQPF_DATA_DIR = os.path.join(ROOT_DIR, 'data/pqpf')

# [ File path]
CONFIG_INI = os.path.join(ROOT_DIR, 'config.ini')

# [ FTP ]
FTP_URL = 'ftp.wpc.ncep.noaa.gov'
FTP_CWD = 'pqpf/conus/pqpf_24hr/'

# [ Regex Patterns]
TODAY = datetime.today().strftime('%Y%m%d')
REG_PATTERN_TODAY = r'{0}'.format(TODAY)
REG_PATTERN_GRB_HOURS = r'f[0-9]+'

# [ Prefixes ]
GRB_PREFIX = 'pqpf_p24i_conus'
TIFF_PREFIX = 'tp'

# [ Projections ]
# WGS84 = 'epsg:4326'

# [ Other ]
VALID_HOURS = ['f030', 'f054', 'f078']
Z_RUN = '06'
TO_HOUR = -6
GRB_RES_X = 2539.703
GRB_RES_Y = 2539.702

# VALID_HOURS = ['f024', 'f048', 'f072']
# Z_RUN = '12'
# TO_HOUR = 0


