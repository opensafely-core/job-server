#!/bin/bash

set -euo pipefail

./manage.py migrate

exec "$@"
