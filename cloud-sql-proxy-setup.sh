#!/bin/sh
# Download Cloud SQL Auth Proxy for local development.
#
# Analysis and web each get their own binary so analysis can run on a separate
# server (and eventually its own repository) without web assets.
#
# Web apps share web/cloud-sql-proxy via Unix socket (/tmp/shellcast-csql/), mirroring GAE.
# Analysis uses TCP on port 3306. Nothing here is deployed per state app.

set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

PROXY_VERSION="v2.22.0"
BASE_URL="https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/${PROXY_VERSION}"

case "$(uname -s)-$(uname -m)" in
  Darwin-arm64) PROXY_BIN="cloud-sql-proxy.darwin.arm64" ;;
  Darwin-x86_64) PROXY_BIN="cloud-sql-proxy.darwin.amd64" ;;
  Linux-x86_64) PROXY_BIN="cloud-sql-proxy.linux.amd64" ;;
  Linux-aarch64) PROXY_BIN="cloud-sql-proxy.linux.arm64" ;;
  *)
    echo "Unsupported platform: $(uname -s) $(uname -m)" >&2
    echo "See https://github.com/GoogleCloudPlatform/cloud-sql-proxy/releases" >&2
    exit 1
    ;;
esac

download_proxy() {
  dest="$1"
  echo "Downloading ${PROXY_BIN} -> ${dest}"
  curl -fsSL "${BASE_URL}/${PROXY_BIN}" -o "${dest}"
  chmod +x "${dest}"
}

# Analysis server / cron (analysis_run.sh uses CLOUD_SQL_PATH from analysis_paths.sh)
download_proxy "${ROOT}/analysis/cloud-sql-proxy"

# Local web dev — one proxy + socket dir for shellcast-web-nc, -sc, and -fl
download_proxy "${ROOT}/web/cloud-sql-proxy"

# Web Unix socket dir (macOS path length limit — use a short path, not web/cloudsql/)
mkdir -p /tmp/shellcast-csql
chmod 777 /tmp/shellcast-csql

echo ""
echo "Done."
echo "  Analysis: ${ROOT}/analysis/cloud-sql-proxy  (TCP, port 3306)"
echo "  Web:      ${ROOT}/web/cloud-sql-proxy         (Unix socket)"
echo "  Web socket dir: /tmp/shellcast-csql/          (set DB_UNIX_SOCKET_PATH_PREFIX in .env)"
