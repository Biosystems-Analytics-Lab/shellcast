#!/bin/sh

# see Releases for other versions
# Go to https://github.com/GoogleCloudPlatform/cloud-sql-proxy
# and get the code snippet for your OS.

# For MacOS Intel
URL="https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.11.4"
curl "$URL/cloud-sql-proxy.darwin.amd64" -o cloud-sql-proxy
chmod +x cloud-sql-proxy

cd ./web/shellcast-web-fl
mkdir cloudsql
chmod 777 ./cloudsql

cd ./web/shellcast-web-nc
mkdir cloudsql
chmod 777 ./cloudsql

cd ./web/shellcast-web-sc
mkdir cloudsql
chmod 777 ./cloudsql
