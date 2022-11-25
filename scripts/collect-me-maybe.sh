#!/bin/bash
set -euo pipefail

# allow just file to pass current venv python through
python=${1:-python}

if ! $python -c 'import django'; then
    echo "Cannot import django - are you in the right virtualenv?"
    exit 1
fi


staticfiles="$($python manage.py print_settings STATIC_ROOT --format value)"
sentinel="$staticfiles/.written"
run=false

if ! test -f "$sentinel"; then
    run=true
else
    staticdirs="$($python manage.py print_settings STATICFILES_DIRS --format value | sed -e "s/[]',[]//g")"
    # shellcheck disable=SC2086
    find $staticdirs -type f -newer "$sentinel" | grep -q . && run=true
fi

if test "$run" = "true"; then
    echo "Run collectstatic, src file changes detected"
    $python manage.py collectstatic --no-input --clear | grep -v '^Deleting '
    touch "$sentinel"
else
    echo "Skipping collectstatic, no changes detected"
fi
