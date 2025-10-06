import os

from services.logging import logging_config_dict
from services.tracing import setup_default_tracing


# Where to log to (stdout and stderr)
accesslog = "-"
errorlog = "-"

# Configure log structure
# http://docs.gunicorn.org/en/stable/settings.html#logconfig-dict
logconfig_dict = logging_config_dict

# workers
workers = 9

# listen
port = 8000
bind = "0.0.0.0"

# request timeout - more than the default of 30 for slow API requests
timeout = 40


def post_fork(server, worker):
    # opentelemetry initialisation needs these env vars to be set, so ensure they are
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jobserver.settings")
    server.log.info("Worker spawned (pid: %s)", worker.pid)
    setup_default_tracing()
