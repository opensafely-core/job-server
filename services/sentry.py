import sentry_sdk
import structlog
from environs import Env
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import ignore_logger


env = Env()
logger = structlog.get_logger(__name__)


def initialise_sentry():  # pragma: no cover
    """
    Initialise Sentry client

    We initialise the client here so as not to pollute global settings with
    poorly named values, ie "dsn".
    """
    dsn = env.str("SENTRY_DSN", default=None)
    environment = env.str("SENTRY_ENVIRONMENT", default="localhost")

    if dsn is None:
        return

    ignore_logger("django_structlog")
    ignore_logger("django_structlog.middlewares.request")

    sentry_sdk.init(
        dsn,
        environment=environment,
        integrations=[DjangoIntegration()],
        send_default_pii=True,
        before_send=strip_sensitive_data,
    )


def monitor_config(schedule):
    return {
        "schedule": {"type": "crontab", "value": f"@{schedule}"},
        "timezone": "Etc/UTC",
        # If an expected check-in doesn't come in `checkin_margin`
        # minutes, it'll be considered missed
        "checkin_margin": 30,
        # The check-in is allowed to run for `max_runtime` minutes
        # before it's considered failed
        "max_runtime": 10,
        # It'll take `failure_issue_threshold` consecutive failed
        # check-ins to create an issue
        "failure_issue_threshold": 1,
        # It'll take `recovery_threshold` OK check-ins to resolve
        # an issue
        "recovery_threshold": 1,
    }


def parse(data):
    if data is None:
        return

    if isinstance(data, bool | int | float):
        return data

    if isinstance(data, dict):
        for k, v in data.items():
            data[k] = parse(v)

    if isinstance(data, list):
        for i, item in enumerate(data):
            data[i] = parse(item)

    # tokens with values we want to strip
    tokens = [
        "GITHUB_TOKEN",
        "GITHUB_TOKEN_TESTING",
        "GITHUB_WRITEABLE_TOKEN",
        "SECRET_KEY",
        "SENTRY_DSN",
        "SOCIAL_AUTH_GITHUB_KEY",
        "SOCIAL_AUTH_GITHUB_SECRET",
    ]

    for token in tokens:
        value = env.str(token, default=None)

        if not value:
            continue

        if value in data:
            data = data.replace(value, "*****")

    return data


def strip_sensitive_data(event, hint):  # pragma: no cover
    try:
        return parse(event)
    except Exception:
        logger.exception()
