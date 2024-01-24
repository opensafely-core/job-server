#!/bin/bash

set -euo pipefail
./manage.py migrate
./scripts/collect-me-maybe.sh
cp -r /opt/assets/. /opt/assetsout/

exec "$@"
