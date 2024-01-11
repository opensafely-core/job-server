#!/usr/bin/env bash
set -euo pipefail

if ! command -v db-to-sqlite &>/dev/null; then
    echo 'db-to-sqlite was not found'
    exit 1
fi

if test -z "${DATABASE_URL:-}"; then
    echo 'DATABASE_URL was not set'
    exit 1
fi

rm -f jobserver.sqlite.zip

db-to-sqlite \
    --progress \
    --table applications_application \
    --table jobserver_project \
    --table jobserver_projectmembership \
    --table jobserver_workspace \
    --table jobserver_user \
    --table jobserver_org \
    --table jobserver_orgmembership \
    --table jobserver_job \
    --table jobserver_jobrequest \
    --table jobserver_release \
    --table jobserver_releasefile \
    ${DATABASE_URL} \
    jobserver.sqlite

# `--move` deletes the uncompressed file after compressing it
zip --move jobserver.sqlite.zip jobserver.sqlite
