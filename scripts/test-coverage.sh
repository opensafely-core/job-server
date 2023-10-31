#!/bin/bash
set -euo pipefail

if command -v coverage; then
    # use coverage on path (if venv activated)
    coverage=$(command -v coverage)
else
    # assume BIN provided by justfile (if not)
    coverage=$BIN/coverage
fi

rc=0
set -x

"$coverage" erase
# shellcheck disable=SC2086
"$coverage" run ${COVERAGE_ARGS:-} --module pytest "$@" || rc=$?
"$coverage" combine --debug=pathmap

# shellcheck disable=SC2086
"$coverage" report ${COVERAGE_REPORT_ARGS:-} || { rc=$?; "$coverage" html ${COVERAGE_REPORT_ARGS:-}; }

exit $rc
