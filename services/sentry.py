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


def parse(data):
    if data is None:
        return

    if isinstance(data, bool | int):
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
    return parse(event)
