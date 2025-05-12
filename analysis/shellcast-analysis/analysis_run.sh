#! /bin/sh

echo $PWD
# source config.sh file (in analysis directory)
source $PWD"/config.sh"

# Function to cleanup Cloud SQL proxy
cleanup_cloud_sql() {
    if [ ! -z "$PID1" ] && kill -0 $PID1 2>/dev/null; then
        echo "Shutting down Cloud SQL proxy..."
        kill -INT $PID1
        wait $PID1 2>/dev/null
    fi
}

# make sure that all spawned processes are killed on exit, a kill signal, or an error
trap "cleanup_cloud_sql; exit" INT TERM ERR
trap "cleanup_cloud_sql; kill 0" EXIT

# open TCP connection for step 4
${CLOUD_SQL_PATH} --port 3306 ${CLOUD_SQL_INSTANCE_NAME} & PID1=$!

source ${VENV_ACTIVATE_PATH}

python $NC_MAIN_PY
python $SC_MAIN_PY
python $FL_MAIN_PY

deactivate

cleanup_cloud_sql

echo "Done"
