set dotenv-load := true

# just has no idiom for setting a default value for an environment variable
# so we shell out, as we need VIRTUAL_ENV in the justfile environment
export VIRTUAL_ENV  := `echo ${VIRTUAL_ENV:-.venv}`

# TODO: make it /scripts on windows?
export BIN := VIRTUAL_ENV + "/bin"
export PIP := BIN + "/python -m pip"
# enforce our chosen pip compile flags
export COMPILE := BIN + "/pip-compile --allow-unsafe --generate-hashes"


# list available commands
default:
    @{{ just_executable() }} --list


check-for-upgrades: devenv
    # run pyupgrade but does not change files
    $BIN/pyupgrade --py39-plus \
        $(find applications -name "*.py" -type f) \
        $(find jobserver -name "*.py" -type f) \
        $(find services -name "*.py" -type f) \
        $(find tests -name "*.py" -type f)

    $BIN/django-upgrade --target-version=3.2 \
        $(find applications -name "*.py" -type f) \
        $(find jobserver -name "*.py" -type f) \
        $(find services -name "*.py" -type f) \
        $(find tests -name "*.py" -type f)


# run the various dev checks but does not change any files
check: devenv format lint sort check-for-upgrades


# clean up temporary files
clean:
    rm -rf .venv


# && dependencies are run after the recipe has run. Needs just>=0.9.9. This is
# a killer feature over Makefiles.
#
# ensure dev requirements installed and up to date
devenv: prodenv requirements-dev && install-precommit
    #!/usr/bin/env bash
    # exit if .txt file has not changed since we installed them (-nt == "newer than', but we negate with || to avoid error exit code)
    test requirements.dev.txt -nt $VIRTUAL_ENV/.dev || exit 0

    $PIP install -r requirements.dev.txt
    touch $VIRTUAL_ENV/.dev


# fix formatting and import sort ordering
fix: devenv
    $BIN/black .
    $BIN/isort .


# runs black but does not change any files
format: devenv
    $BIN/black --check .


# ensure precommit is installed
install-precommit:
    #!/usr/bin/env bash
    BASE_DIR=$(git rev-parse --show-toplevel)
    test -f $BASE_DIR/.git/hooks/pre-commit || $BIN/pre-commit install


# runs flake8 but does not change any files
lint: devenv
    $BIN/flake8


# ensure prod requirements installed and up to date
prodenv: requirements-prod
    #!/usr/bin/env bash
    # exit if .txt file has not changed since we installed them (-nt == "newer than', but we negate with || to avoid error exit code)
    test requirements.prod.txt -nt $VIRTUAL_ENV/.prod || exit 0

    $PIP install -r requirements.prod.txt
    touch $VIRTUAL_ENV/.prod


# update requirements.dev.txt if requirements.dev.in has changed
requirements-dev: requirements-prod
    #!/usr/bin/env bash
    # exit if .in file is older than .txt file (-nt = 'newer than', but we negate with || to avoid error exit code)
    test requirements.dev.in -nt requirements.dev.txt || exit 0
    $COMPILE --output-file=requirements.dev.txt requirements.dev.in


# update requirements.prod.txt if requirement.prod.in has changed
requirements-prod: virtualenv
    #!/usr/bin/env bash
    # exit if .in file is older than .txt file (-nt = 'newer than', but we negate with || to avoid error exit code)
    test requirements.prod.in -nt requirements.prod.txt || exit 0
    $COMPILE --output-file=requirements.prod.txt requirements.prod.in


# runs isort but does not change any files
sort: devenv
    $BIN/isort --check-only --diff .


# Run the dev project
run: devenv
    $BIN/python manage.py runserver


# *ARGS is variadic, 0 or more. This allows us to do `just test -k match`, for example.
# Run the tests
test *ARGS: devenv
    $BIN/python manage.py collectstatic --no-input
    $BIN/python -m pytest \
        --cov=applications \
        --cov=jobserver \
        --cov=staff \
        --cov=services \
        --cov=tests \
        --cov-report=html \
        --cov-report=term-missing:skip-covered \
        {{ ARGS }}


# upgrade dev or prod dependencies (all by default, specify package to upgrade single package)
upgrade env package="": virtualenv
    #!/usr/bin/env bash
    opts="--upgrade"
    test -z "{{ package }}" || opts="--upgrade-package {{ package }}"
    $COMPILE $opts --output-file=requirements.{{ env }}.txt requirements.{{ env }}.in


# ensure valid virtualenv
virtualenv:
    #!/usr/bin/env bash
    # allow users to specify python version in .env
    PYTHON_VERSION=${PYTHON_VERSION:-python3.9}

    # create venv and upgrade pip
    test -d $VIRTUAL_ENV || { $PYTHON_VERSION -m venv $VIRTUAL_ENV && $PIP install --upgrade pip; }

    # ensure we have pip-tools so we can run pip-compile
    test -e $BIN/pip-compile || $PIP install pip-tools
