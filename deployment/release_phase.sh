#!/usr/bin/env bash
# Commands run during the release phase after build but before deploy.
# https://dokku.com/docs/processes/process-management/#the-release-process
# https://devcenter.heroku.com/articles/release-phase

set -euo pipefail

./manage.py check --deploy
./manage.py migrate
