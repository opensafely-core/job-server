import logging
import warnings

import structlog
from environs import Env


# add logging before app has booted
env = Env()
DEBUG = env.bool("DEBUG", default=False)


def timestamper(logger, log_method, event_dict):
    """
    Add timestamps to logs conditionally

    Structlog provides a Timestamper processor.  However, we only want to
    timestamp logs locally since Production stamps logs for us.  This mirrors
    how the Timestamper processor stamps events internally.
    """
    if not DEBUG:
        return event_dict

    # mirror how structlogs own Timestamper calls _make_stamper
    stamper = structlog.processors._make_stamper(fmt="iso", utc=True, key="timestamp")
    return stamper(event_dict)


pre_chain = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    # Add the log level and a timestamp to the event_dict if the log entry
    # is not from structlog.
    timestamper,
]

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        timestamper,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.ExceptionPrettyPrinter(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
)


class MissingVariableErrorFilter(logging.Filter):
    """
    Convert "missing template variable" log messages into warnings.

    Heavily inspired by Adam Johnson's work here:
    https://adamj.eu/tech/2022/03/30/how-to-make-django-error-for-undefined-template-variables/
    """

    ignored_prefixes = (
        # Some of Django's internal templates rely on the silent missing template
        # variable behaviour
        "admin/",
        "auth/",
        "django/",
        # As does our internal component library
        "_components",
        "_partials",
        # As do two of our internal applications
        "applications/",
        "interactive/",
    )
    ignored_variable_names = {
        # Some template variables are added by middleware, and so
        # are missing when pages are requested by a `RequestFactory` instance.
        "csp_nonce",  # csp.middleware.CSPMiddleware
        "template_name",  # jobserver.middleware.TemplateNameMiddleware
    }

    def filter(self, record):  # pragma: no cover
        if record.msg.startswith("Exception while resolving variable "):
            variable_name, template_name = record.args
            if (
                not template_name.startswith(self.ignored_prefixes)
                # This shows up when rendering Django's internal error pages
                and template_name != "unknown"
                and variable_name not in self.ignored_variable_names
            ):
                # We use `warn_explicit` to raise the warning at whatever location the
                # original log message was raised
                warnings.warn_explicit(
                    record.getMessage(), UserWarning, record.pathname, record.lineno
                )
        return False


logging_config_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "formatter": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(),
            "foreign_pre_chain": pre_chain,
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "formatter",
        }
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "filters": {
        "missing_variable_error": {
            "()": f"{MissingVariableErrorFilter.__module__}.{MissingVariableErrorFilter.__name__}"
        }
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": env.str("DJANGO_LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
        "django.template": {
            "level": "DEBUG",
            "filters": ["missing_variable_error"],
        },
        "gunicorn.access": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "gunicorn.error": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django_structlog": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "applications": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "jobserver": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "services": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "staff": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
