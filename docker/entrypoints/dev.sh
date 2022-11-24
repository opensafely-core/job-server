#!/bin/bash

set -euo pipefail

./manage.py migrate
./manage.py ensure_admins
./scripts/collect-me-maybe.sh

exec "$@"
