#!/usr/bin/env bash
set -euo pipefail

echo "Running EarlyBird pre-commit hook"

if ! command -v just >/dev/null 2>&1; then
  echo "'just' is required. Install it and retry." >&2
  exit 1
fi

if ! just earlybird-check --git-staged --fail-severity=high; then
  echo "EarlyBird checks must pass before commit!" >&2
  exit 1
fi
