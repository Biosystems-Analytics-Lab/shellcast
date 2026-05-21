#! /bin/sh
# Machine-specific paths for analysis_run.sh (cron).
# Copy to analysis_paths.sh and edit paths for this computer.
# Python settings (DB, shapefiles, email) live in analysis_settings.ini instead.

# Path to cloud_sql_proxy file
CLOUD_SQL_PATH="{your directory}/shellcast/analysis/shellcast-analysis/cloud-sql-proxy"

# Name of Cloud SQL Instance
CLOUD_SQL_INSTANCE_NAME=""

# MySQL port
CLOUD_SQL_PORT="3306"

VENV_ACTIVATE_PATH="{path to virtual environment activate}"

FL_MAIN_PY="/{your directory}/shellcast/analysis/shellcast-analysis/fl_main.py"
NC_MAIN_PY="/{your directory}/shellcast/analysis/shellcast-analysis/nc_main.py"
SC_MAIN_PY="/{your directory}/shellcast/analysis/shellcast-analysis/sc_main.py"
