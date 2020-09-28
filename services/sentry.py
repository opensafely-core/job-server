import os

import sentry_sdk
import structlog
from sentry_sdk.integrations.django import DjangoIntegration


logger = structlog.get_logger(__name__)


def initialise_sentry():
    """
    Initialise Sentry client

    We initialise the client here so as not to pollute global settings with
    poorly named values, ie "dsn".
    """
    dsn = os.getenv("SENTRY_DSN", default=None)
    environment = os.getenv("SENTRY_ENVIRONMENT", default="localhost")

    if dsn is None:
        return

    sentry_sdk.init(
        dsn,
        environment=environment,
        integrations=[DjangoIntegration()],
        send_default_pii=True,
    )
