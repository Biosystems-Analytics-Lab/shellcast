#!/usr/bin/env bash

set -euo pipefail

# Usage: ./run-web.sh <state>
# Example: ./run-web.sh sc

STATE="${1:-}"
if [[ -z "${STATE}" ]]; then
  echo "Usage: $0 <state>"
  echo "Example: $0 sc"
  exit 1
fi

# Normalize to lowercase (portable, works on older macOS Bash)
STATE="$(printf "%s" "${STATE}" | tr '[:upper:]' '[:lower:]')"

# Map state to web directory
WEB_DIR="web/shellcast-web-${STATE}"
if [[ ! -d "${WEB_DIR}" ]]; then
  echo "Error: ${WEB_DIR} not found. Valid states are likely: nc, sc, fl"
  exit 1
fi

# Cloud SQL instance (shared across environments)
INSTANCE_CONNECTION_NAME="ncsu-shellcast:us-east1:ncsu-shellcast-database"

# Proxy binary and unix socket dir
PROXY_BIN="${WEB_DIR}/cloudsql/cloud-sql-proxy"
SOCKET_DIR="${WEB_DIR}/cloudsql"

if [[ ! -x "${PROXY_BIN}" ]]; then
  if [[ -f "${PROXY_BIN}" ]]; then
    chmod +x "${PROXY_BIN}"
  else
    echo "Error: Cloud SQL Proxy binary not found at ${PROXY_BIN}"
    echo "Hint: Place the proxy binary there or adjust this script."
    exit 1
  fi
fi

# Ensure web venv exists
WEB_VENV="web/webvenv/bin/activate"
if [[ ! -f "${WEB_VENV}" ]]; then
  echo "Error: Web virtual environment not found at ${WEB_VENV}"
  echo "Hint: Create it or adjust the path in this script."
  exit 1
fi

cleanup() {
  local exit_code=$?
  if [[ -n "${PROXY_PID:-}" ]] && ps -p "${PROXY_PID}" > /dev/null 2>&1; then
    echo "Stopping Cloud SQL Proxy (pid=${PROXY_PID})..."
    kill "${PROXY_PID}" || true
    # Give it a moment to shutdown cleanly
    wait "${PROXY_PID}" 2>/dev/null || true
  fi
  echo "Stopping Cloud SQL Proxy --- Done"
  exit ${exit_code}
}
trap cleanup INT TERM EXIT

echo "Starting Cloud SQL Proxy (unix socket) for state=${STATE}..."
"${PROXY_BIN}" --unix-socket "${SOCKET_DIR}" "${INSTANCE_CONNECTION_NAME}" &
PROXY_PID=$!
echo "Cloud SQL Proxy started (pid=${PROXY_PID})."

echo "Activating webvenv..."
source "${WEB_VENV}"

echo "Running Flask app for ${STATE}..."
pushd "${WEB_DIR}" >/dev/null
python main.py
popd >/dev/null

# Normal exit path triggers trap/cleanup

