#! /bin/sh

# source config.sh file (in analysis directory)
source ./config.sh

# make sure that all spawned processes are killed on exit, a kill signal, or an error
trap "exit" INT TERM ERR
trap "kill 0" EXIT

# open TCP connection for step 4
${CLOUD_SQL_PATH} --port 3306 ${CLOUD_SQL_INSTANCE_NAME} & PID1=$!

source ${VENV_ACTIVATE_PATH}

python $FL_MAIN_PY
python $NC_MAIN_PY
python $SC_MAIN_PY

deactivate

echo $PID1

kill -INT $PID1
