#!/bin/bash

set -euo pipefail

./manage.py migrate
./manage.py collectstatic --no-input

exec "$@"
