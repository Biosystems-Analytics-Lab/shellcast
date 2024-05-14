#!/bin/sh

# Unix socket connection - shellcast-web-{state}

# NC
./cloud-sql-proxy --unix-socket "./web/shellcast-web-nc/cloudsql" "{instance_connection_name}"

# SC
./cloud-sql-proxy --unix-socket "./web/shellcast-web-sc/cloudsql" "{instance_connection_name}"

# FL
./cloud-sql-proxy --unix-socket "./web/shellcast-web-fl/cloudsql" "{instance_connection_name}"