from services.logging import logging_config_dict


# Where to log to (stdout and stderr)
accesslog = "-"
errorlog = "-"

# Configure log structure
# http://docs.gunicorn.org/en/stable/settings.html#logconfig-dict
logconfig_dict = logging_config_dict

# workers
workers = 3


def post_fork(server, worker):
    from opentelemetry.instrumentation.auto_instrumentation import (  # noqa: F401
        sitecustomize,
    )
