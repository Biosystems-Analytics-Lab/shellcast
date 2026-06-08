#!/bin/sh
# Run from repo root: ./my-cloud-sql-proxy.sh [analysis|web]
# Do not use "source" — this script exec's the proxy and replaces the process.
#
# Setup:
#   cp my-cloud-sql-proxy.template.sh my-cloud-sql-proxy.sh
#   Edit instance_connection_name (Cloud Console → SQL → Connection name)
#   chmod +x my-cloud-sql-proxy.sh

ROOT="$(cd "$(dirname "$0")" && pwd)"
instance_connection_name="your-project:region:instance-name"

mode="${1:-web}"

case "$mode" in
  analysis|tcp)
    PROXY="${ROOT}/analysis/cloud-sql-proxy"
    ;;
  web|nc|sc|fl)
    PROXY="${ROOT}/web/cloud-sql-proxy"
    # macOS sun_path limit is 104 chars; repo path + instance name exceeds it.
    SOCKET_DIR="${SHELLCAST_CLOUDSQL_DIR:-/tmp/shellcast-csql}"
    mkdir -p "${SOCKET_DIR}"
    chmod 777 "${SOCKET_DIR}"
    ;;
  *)
    echo "Usage: $0 [analysis|web]" >&2
    echo "  analysis - TCP port 3306 (analysis)" >&2
    echo "  web      - Unix socket (all shellcast-web-* apps)" >&2
    exit 1
    ;;
esac

if [ ! -x "${PROXY}" ]; then
  echo "Missing ${PROXY}" >&2
  echo "Run: sh cloud-sql-proxy-setup.sh" >&2
  exit 127
fi

case "$mode" in
  analysis|tcp)
    exec "${PROXY}" --port 3306 "${instance_connection_name}"
    ;;
  web|nc|sc|fl)
    exec "${PROXY}" --unix-socket "${SOCKET_DIR}" "${instance_connection_name}"
    ;;
esac
