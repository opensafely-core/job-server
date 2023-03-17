set dotenv-load := true

# just has no idiom for setting a default value for an environment variable
# so we shell out, as we need VIRTUAL_ENV in the justfile environment
export VIRTUAL_ENV  := `echo ${VIRTUAL_ENV:-.venv}`

# TODO: make it /scripts on windows?
export BIN := VIRTUAL_ENV + "/bin"
export PIP := BIN + "/python -m pip"

# list available commands
default:
    @{{ just_executable() }} --list


# clean up temporary files
clean:
    rm -rf .venv


# ensure valid virtualenv
virtualenv: _env
    #!/usr/bin/env bash
    # allow users to specify python version in .env
    PYTHON_VERSION=${PYTHON_VERSION:-python3.11}

    # create venv and upgrade pip
    test -d $VIRTUAL_ENV || { $PYTHON_VERSION -m venv $VIRTUAL_ENV && $PIP install --upgrade pip; }

    # ensure we have pip-tools so we can run pip-compile
    test -e $BIN/pip-compile || $PIP install pip-tools


_env:
    #!/usr/bin/env bash
    test -f .env || cp dotenv-sample .env


_compile src dst *args: virtualenv
    #!/usr/bin/env bash
    # exit if src file is older than dst file (-nt = 'newer than', but we negate with || to avoid error exit code)
    test "${FORCE:-}" = "true" -o {{ src }} -nt {{ dst }} || exit 0
    $BIN/pip-compile --allow-unsafe --generate-hashes --strip-extras --output-file={{ dst }} {{ src }} {{ args }}


# update requirements.prod.txt if requirements.prod.in has changed
requirements-prod *args:
    {{ just_executable() }} _compile requirements.prod.in requirements.prod.txt {{ args }}


# update requirements.dev.txt if requirements.dev.in has changed
requirements-dev *args: requirements-prod
    {{ just_executable() }} _compile requirements.dev.in requirements.dev.txt {{ args }}


# ensure prod requirements installed and up to date
prodenv: requirements-prod
    #!/usr/bin/env bash
    set -eux
    # exit if .txt file has not changed since we installed them (-nt == "newer than', but we negate with || to avoid error exit code)
    test requirements.prod.txt -nt $VIRTUAL_ENV/.prod || exit 0

    # --no-deps is recommended when using hashes, and also worksaround a bug with constraints and hashes.
    # https://pip.pypa.io/en/stable/topics/secure-installs/#do-not-use-setuptools-directly
    $PIP install --no-deps -r requirements.prod.txt
    touch $VIRTUAL_ENV/.prod


# && dependencies are run after the recipe has run. Needs just>=0.9.9. This is
# a killer feature over Makefiles.
#
# ensure dev requirements installed and up to date
devenv: prodenv requirements-dev && install-precommit
    #!/usr/bin/env bash
    set -eu
    # exit if .txt file has not changed since we installed them (-nt == "newer than', but we negate with || to avoid error exit code)
    test requirements.dev.txt -nt $VIRTUAL_ENV/.dev || exit 0

    # --no-deps is recommended when using hashes, and also worksaround a bug with constraints and hashes.
    # https://pip.pypa.io/en/stable/topics/secure-installs/#do-not-use-setuptools-directly
    $PIP install --no-deps -r requirements.dev.txt
    touch $VIRTUAL_ENV/.dev


# ensure precommit is installed
install-precommit:
    #!/usr/bin/env bash
    BASE_DIR=$(git rev-parse --show-toplevel)
    test -f $BASE_DIR/.git/hooks/pre-commit || $BIN/pre-commit install


# upgrade dev or prod dependencies (specify package to upgrade single package, all by default)
upgrade env package="": virtualenv
    #!/usr/bin/env bash
    opts="--upgrade"
    test -z "{{ package }}" || opts="--upgrade-package {{ package }}"
    FORCE=true {{ just_executable() }} requirements-{{ env }} $opts


# Run the dev project with telemetry
run-telemetry: devenv
    $BIN/opentelemetry-instrument $BIN/python manage.py runserver --noreload


test-base *args: assets
    $BIN/coverage run --module pytest {{ args }}


test-dev *args:
    {{ just_executable() }} test-base \
        '-m "not verification and not slow_test"' \
        {{ args }}

    # run with || so they both run regardless of failures
    $BIN/coverage report --omit=interactive/opencodelists.py,jobserver/github.py,tests/integration/test_interactive.py,"tests/verification/*" \
    || $BIN/coverage html --omit=interactive/opencodelists.py,jobserver/github.py,tests/integration/test_interactive.py,"tests/verification/*"


test *args:
    {{ just_executable() }} test-base {{ args }}

    $BIN/coverage report || $BIN/coverage html


black *args=".": devenv
    $BIN/black --check {{ args }}

isort *args=".": devenv
    $BIN/isort --check-only --diff {{ args }}

flake8 *args="": devenv
    $BIN/flake8 {{ args }}

pyupgrade *args="$(find applications interactive jobserver redirects services staff tests -name '*.py' -type f)": devenv
    $BIN/pyupgrade --py311-plus {{ args }}

django-upgrade *args="$(find applications interactive jobserver redirects services staff tests -name '*.py' -type f)": devenv
    $BIN/django-upgrade --target-version=3.2 {{ args }}

# run the various dev checks but does not change any files
check: black isort flake8 pyupgrade django-upgrade


check-migrations: devenv
    $BIN/python manage.py makemigrations --dry-run --check


# fix formatting and import sort ordering
fix: devenv
    $BIN/black .
    $BIN/isort .


load-dev-data: devenv
    $BIN/python manage.py loaddata backends


# Run the dev project
run: devenv
    $BIN/python manage.py migrate
    $BIN/python manage.py runserver localhost:8000


run-prod: prodenv
    $BIN/gunicorn -c gunicorn.conf.py jobserver.wsgi


# Remove built assets and collected static files
assets-clean:
    rm -rf assets/dist
    rm -rf staticfiles


# Install the Node.js dependencies
assets-install:
    #!/usr/bin/env bash
    set -eu

    # exit if lock file has not changed since we installed them. -nt == "newer than",
    # but we negate with || to avoid error exit code
    test package-lock.json -nt node_modules/.written || exit 0

    npm ci
    touch node_modules/.written


# Build the Node.js assets
assets-build:
    #!/usr/bin/env bash
    set -eu

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

# install npm toolchaing, build and collect assets
assets: assets-install assets-build collectstatic

# rebuild all npm/static assets
assets-rebuild: assets-clean assets


# run a local release hatch instance, including adding and configuring a backend to use with it.
release-hatch:
    ./scripts/local-release-hatch.sh

# note these are just aliases for the docker/justfile commands. We add them just for autocompletion from the root dir

# build docker image env=dev|prod
docker-build env="dev": _env
    {{ just_executable() }} docker/build {{ env }}


# run tests in the dev docker container
docker-test *args="": _env
    {{ just_executable() }} docker/test {{ args }}


# run server in dev or prod docker container
docker-serve env="dev" *args="": _env
    {{ just_executable() }} docker/serve {{ env }} {{ args }}


# run cmd in dev or prod docker container
docker-run env="dev" *args="bash": _env
    {{ just_executable() }} docker/run {{ env }} {{ args }}


# exec command in an existing dev docker container
docker-exec env="dev" *args="bash": _env
    {{ just_executable() }} docker/exec {{ env }} {{ args }}


# run basic smoke test against a running job-server
docker-smoke-test host="http://localhost:8000": _env
    {{ just_executable() }} docker/smoke-test {{ host }}
