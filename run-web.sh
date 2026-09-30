#!/usr/bin/env bash

set -euo pipefail

# Usage: ./run-web.sh <state>
# Example: ./run-web.sh sc
#
# Starts the shared web Cloud SQL proxy, then the Flask app for that state.
# Ctrl+C stops Flask and the proxy.

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "${ROOT}"

STATE="${1:-}"
if [[ -z "${STATE}" ]]; then
  echo "Usage: $0 <state>"
  echo "Example: $0 sc"
  exit 1
fi

STATE="$(printf "%s" "${STATE}" | tr '[:upper:]' '[:lower:]')"

WEB_DIR="web/shellcast-web-${STATE}"
if [[ ! -d "${WEB_DIR}" ]]; then
  echo "Error: ${WEB_DIR} not found. Valid states: nc, sc, fl"
  exit 1
fi

INSTANCE_CONNECTION_NAME="ncsu-shellcast:us-east1:ncsu-shellcast-database"
SOCKET_DIR="${SHELLCAST_CLOUDSQL_DIR:-/tmp/shellcast-csql}"

if [[ -f "${WEB_DIR}/.env" ]]; then
  env_instance="$(grep -E '^CLOUD_SQL_INSTANCE_NAME=' "${WEB_DIR}/.env" | head -1 | cut -d= -f2- | tr -d '"' || true)"
  env_socket="$(grep -E '^DB_UNIX_SOCKET_PATH_PREFIX=' "${WEB_DIR}/.env" | head -1 | cut -d= -f2- | tr -d '"' || true)"
  if [[ -n "${env_instance}" ]]; then
    INSTANCE_CONNECTION_NAME="${env_instance}"
  fi
  if [[ -n "${env_socket}" ]]; then
    SOCKET_DIR="${env_socket%/}"
  fi
fi

PROXY_BIN="${ROOT}/web/cloud-sql-proxy"
if [[ ! -x "${PROXY_BIN}" ]]; then
  if [[ -f "${PROXY_BIN}" ]]; then
    chmod +x "${PROXY_BIN}"
  else
    echo "Error: Cloud SQL Proxy binary not found at ${PROXY_BIN}"
    echo "Hint: from the repo root, run: sh cloud-sql-proxy-setup.sh"
    exit 1
  fi
fi

WEB_VENV="${ROOT}/web/venv/bin/activate"
if [[ ! -f "${WEB_VENV}" ]]; then
  echo "Error: Web virtual environment not found at ${WEB_VENV}"
  echo "Hint: cd web && python3 -m venv venv && source venv/bin/activate && pip install -r shellcast-web-nc/requirements.txt"
  exit 1
fi

mkdir -p "${SOCKET_DIR}"
chmod 777 "${SOCKET_DIR}"
SOCKET_PATH="${SOCKET_DIR}/${INSTANCE_CONNECTION_NAME}"

cleanup() {
  local exit_code=$?
  if [[ -n "${PROXY_PID:-}" ]] && ps -p "${PROXY_PID}" > /dev/null 2>&1; then
    echo "Stopping Cloud SQL Proxy (pid=${PROXY_PID})..."
    kill "${PROXY_PID}" || true
    wait "${PROXY_PID}" 2>/dev/null || true
  fi
  exit "${exit_code}"
}
trap cleanup INT TERM EXIT

echo "Starting Cloud SQL Proxy (unix socket ${SOCKET_DIR}) for state=${STATE}..."
"${PROXY_BIN}" --unix-socket "${SOCKET_DIR}" "${INSTANCE_CONNECTION_NAME}" &
PROXY_PID=$!

ready=0
for _ in $(seq 1 50); do
  if [[ -S "${SOCKET_PATH}" ]]; then
    ready=1
    break
  fi
  if ! ps -p "${PROXY_PID}" > /dev/null 2>&1; then
    echo "Error: Cloud SQL Proxy exited before the socket was ready."
    exit 1
  fi
  sleep 0.2
done
if [[ "${ready}" -ne 1 ]]; then
  echo "Error: Timed out waiting for ${SOCKET_PATH}"
  exit 1
fi
echo "Cloud SQL Proxy ready (pid=${PROXY_PID})."

if [[ -z "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]]; then
  echo "Note: GOOGLE_APPLICATION_CREDENTIALS is not set. Sign-in will fail until you export the Firebase Admin JSON path."
fi

echo "Activating web venv..."
# shellcheck disable=SC1090
source "${WEB_VENV}"

echo "Running Flask app for ${STATE}..."
cd "${WEB_DIR}"
python main.py
