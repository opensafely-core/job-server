#!/bin/bash

set -euo pipefail
./manage.py migrate
./manage.py ensure_admins
./scripts/collect-me-maybe.sh
cp -r /opt/assets/. /opt/assetsout/

exec "$@"
