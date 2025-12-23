set dotenv-load := true

export VIRTUAL_ENV  := env_var_or_default("VIRTUAL_ENV", ".venv")

export BIN := VIRTUAL_ENV + if os_family() == "unix" { "/bin" } else { "/Scripts" }


# list available commands
default:
    @{{ just_executable() }} --list


# clean up temporary files
clean:
    rm -rf .venv


# create a default .env file
_dotenv:
    #!/usr/bin/env bash
    set -euo pipefail

    if [[ ! -f .env ]]; then
      echo "No '.env' file found; creating a default '.env' from 'dotenv-sample'"
      cp dotenv-sample .env
    fi


# Install production requirements into venv.
prodenv:
    #!/usr/bin/env bash
    set -euxo pipefail

    # Ensure all project dependencies are installed and up-to-date with
    # the lockfile. The project is re-locked before syncing, so any
    # changes to pyproject.toml are reflected in the environment
    # (https://docs.astral.sh/uv/concepts/projects/sync/#locking-and-syncing).
    # Disable the dev dependency group (--no-dev) and remove any
    # extraneous packages (default uv sync behaviour)
    # (https://docs.astral.sh/uv/reference/cli/#uv-sync)
    uv sync --no-dev

# && dependencies are run after the recipe has run. Needs just>=0.9.9. # This is a killer feature over Makefiles.
# Install dev requirements into venv.
devenv: _dotenv && install-precommit
    #!/usr/bin/env bash
    set -euo pipefail

    # Ensure all project dependencies are installed and up-to-date with
    # the lockfile. The project is re-locked before syncing, so any
    # changes to pyproject.toml are reflected in the environment
    # (https://docs.astral.sh/uv/concepts/projects/sync/#locking-and-syncing).
    # Do not remove extraneous packages (--inexact)
    # (https://docs.astral.sh/uv/reference/cli/#uv-sync--inexact)
    uv sync --inexact

# ensure precommit is installed
install-precommit:
    #!/usr/bin/env bash
    set -euo pipefail

    BASE_DIR=$(git rev-parse --show-toplevel)
    test -f $BASE_DIR/.git/hooks/pre-commit || $BIN/pre-commit install


# Upgrade a single package to the latest version per pyproject.toml
upgrade-package package: && devenv
    uv lock --upgrade-package {{ package }}


# Move the cutoff date in pyproject.toml to N days ago (default: 7) at midnight UTC
bump-uv-cutoff days="7":
    #!/usr/bin/env -S uvx --with tomlkit python3.13
    # Note we specify the python version here and we don't care if it's different to
    # the .python-version; we need 3.11+ for the datetime code used.

    import datetime
    import tomlkit

    with open("pyproject.toml", "rb") as f:
        content = tomlkit.load(f)

    new_datetime = (
        datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=int("{{ days }}"))
    ).replace(hour=0, minute=0, second=0, microsecond=0)
    new_timestamp = new_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
    if existing_timestamp := content["tool"]["uv"].get("exclude-newer"):
        if new_datetime < datetime.datetime.fromisoformat(existing_timestamp):
            print(
                f"Existing cutoff {existing_timestamp} is more recent than {new_timestamp}, not updating."
            )
            exit(0)
    content["tool"]["uv"]["exclude-newer"] = new_timestamp

    with open("pyproject.toml", "w") as f:
        tomlkit.dump(content, f)

# This is the default input command to update-dependencies action
# https://github.com/bennettoxford/update-dependencies-action

# Upgrade all packages to the latest version per pyproject.toml, then
# update the local venv. NOTE: This does not upgrade the opensafely-pipeline;
# to upgrade, run the upgrade-pipeline recipe
# Bump the timestamp cutoff to midnight UTC 7 days ago and upgrade all dependencies
update-dependencies: bump-uv-cutoff && devenv
    uv lock --upgrade

# upgrade our internal pipeline library
upgrade-pipeline: && prodenv
    ./scripts/upgrade-pipeline.sh pyproject.toml


# Run the dev project with telemetry
run-telemetry: devenv
    $BIN/opentelemetry-instrument $BIN/python manage.py runserver --noreload

# run a Django management command
manage command *args:
    $BIN/python manage.py {{command}} {{args}}

test-ci *args: assets
    #!/bin/bash
    export COVERAGE_PROCESS_START="pyproject.toml"
    export COVERAGE_REPORT_ARGS="--omit=jobserver/github.py,jobserver/opencodelists.py,tests/fakes.py,tests/verification/*,tests/functional/*"
    ./scripts/test-coverage.sh -m "not verification and not functional" {{ args }}

# Run the Python functional tests, using Playwright.
test-functional *ARGS: devenv
    $BIN/python manage.py collectstatic --no-input && \
    $BIN/python -m pytest \
    -m "functional" {{ ARGS }}

test-verification *args: devenv
    #!/bin/bash
    export COVERAGE_PROCESS_START="pyproject.toml"
    export COVERAGE_REPORT_ARGS="--include=jobserver/github.py,jobserver/opencodelists.py,tests/fakes.py,tests/verification/*"
    ./scripts/test-coverage.sh -m "verification" {{ args }}

test *args: assets
    $BIN/pytest -n auto -m "not verification and not slow_test and not functional" {{ args }}

format *args=".": devenv
    $BIN/ruff format --check {{ args }}


django-upgrade *args="$(find applications jobserver redirects services staff tests -name '*.py' -type f)": devenv
    $BIN/django-upgrade --target-version=5.0 {{ args }}


lint *args=".": devenv
    $BIN/ruff check --output-format=full {{ args }}
    $BIN/djhtml --tabwidth 2 --check templates/


# validate uv.lock
check-lockfile:
    #!/usr/bin/env bash
    set -euo pipefail
    # Make sure dates in pyproject.toml and uv.lock are in sync
    unset UV_EXCLUDE_NEWER
    rc=0
    uv lock --check || rc=$?
    if test "$rc" != "0" ; then
        echo "Timestamp cutoffs in uv.lock must match those in pyproject.toml. See DEVELOPERS.md for details and hints." >&2
        exit $rc
    fi


# run the various dev checks but does not change any files
check: check-lockfile format django-upgrade lint


check-migrations: devenv
    $BIN/python manage.py makemigrations --dry-run --check \
    || echo "There is model state unaccounted for in the migrations, run `just migrate` to fix."

# generate migrations for any model changes
make-migrations: devenv
    $BIN/python manage.py makemigrations

# apply any unapplied migrations
apply-migrations: devenv
    $BIN/python manage.py migrate

# generate migrations and apply unapplied ones
migrate: make-migrations apply-migrations

# fix the things we can automate: linting, formatting, import sorting
fix: devenv
    $BIN/ruff check --fix .
    $BIN/ruff format .
    $BIN/djhtml --tabwidth 2 templates/


load-dev-data: devenv
    $BIN/python manage.py loaddata backends


# Run the dev project
run bind="localhost:8000": devenv
    $BIN/python manage.py migrate
    DJANGO_DEBUG_TOOLBAR=True $BIN/python manage.py runserver {{ bind }}


# Run the rap status service to fetch job updates from the RAP API
run-rapstatus: devenv
    $BIN/python manage.py rap_status_service

# Run the dev server and the rap_status_service together
run-all:
    { just run & just run-rapstatus; }


run-prod: prodenv
    $BIN/gunicorn -c gunicorn.conf.py jobserver.wsgi


# Remove built assets and collected static files
assets-clean:
    rm -rf assets/dist
    rm -rf staticfiles


# Install the Node.js dependencies
assets-install *args="":
    #!/usr/bin/env bash
    set -euo pipefail


    # exit if lock file has not changed since we installed them. -nt == "newer than",
    # but we negate with || to avoid error exit code
    test package-lock.json -nt node_modules/.written || exit 0

    npm ci {{ args }}
    touch node_modules/.written


# Build the Node.js assets
assets-build:
    #!/usr/bin/env bash
    set -euo pipefail


    # find files which are newer than dist/.written in the src directory. grep
    # will exit with 1 if there are no files in the result.  We negate this
    # with || to avoid error exit code
    # we wrap the find in an if in case dist/.written is missing so we don't
    # trigger a failure prematurely
    if test -f assets/dist/.written; then
        find assets/src -type f -newer assets/dist/.written | grep -q . || exit 0
    fi

    npm run build
    touch assets/dist/.written


# Ensure django's collectstatic is run if needed
collectstatic: devenv
    ./scripts/collect-me-maybe.sh $BIN/python

# install npm toolchain, build and collect assets
assets: assets-install assets-build collectstatic

# rebuild all npm/static assets
assets-rebuild: assets-clean assets

assets-run: assets-install
    #!/usr/bin/env bash
    set -euo pipefail

    if [ "$ASSETS_DEV_MODE" == "False" ]; then
        echo "Set ASSETS_DEV_MODE to a truthy value to run this command"
        exit 1
    fi

    npm run dev


assets-test: assets-install
    npm run test:coverage


# dump data for co-pilot reporting to a compressed SQLite database
dump-co-pilot-reporting-data:
    ./scripts/dump-co-pilot-reporting-data.sh

# The docker-* commands are simply aliases for the docker/justfile commands.
# We add them for autocompletion from the root dir.

# build docker image env=dev|prod
docker-build env="dev":
    {{ just_executable() }} docker/build {{ env }}


# run python non-functional tests in the dev docker container
docker-test-py *args="":
    {{ just_executable() }} docker/test-py {{ args }}

# run functional tests in docker container
docker-test-functional *args="":
    {{ just_executable() }} docker/test-functional {{ args }}

# run server in dev or prod docker container
docker-serve env="dev" *args="":
    {{ just_executable() }} docker/serve {{ env }} {{ args }}


# run cmd in dev or prod docker container
docker-run env="dev" *args="":
    {{ just_executable() }} docker/run {{ env }} {{ args }}


# exec command in an existing dev docker container
docker-exec env="dev" *args="bash":
    {{ just_executable() }} docker/exec {{ env }} {{ args }}


# run basic smoke test against a running job-server
docker-smoke-test host="http://localhost:8000":
    {{ just_executable() }} docker/smoke-test {{ host }}
