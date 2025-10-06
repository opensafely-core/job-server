#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys

from services.tracing import setup_default_tracing


def main():
    # Disable Sentry when running the shell. This is mainly used by devs to
    # interrogate the database and typing code manually is error-prone.
    # Unhandled exceptions caused by this activity are unlikely to be
    # interesting, so let us not raise Sentry issues in this case.
    if len(sys.argv) > 1 and sys.argv[1] == "shell":
        os.environ.pop("SENTRY_DSN", None)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jobserver.settings")
    setup_default_tracing()

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
