#!/bin/sh

# Unix socket connection - shellcast-web-{state}
instance_connection_name="{Find the instance connection name in the Google Cloud Console}"

# Modify {state} to the state of the web application.
./cloud-sql-proxy --unix-socket "./web/shellcast-web-{state}/cloudsql" ${instance_connection_name}
