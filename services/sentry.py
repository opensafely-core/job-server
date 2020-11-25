import sentry_sdk
import structlog
from environs import Env
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import ignore_logger


env = Env()
logger = structlog.get_logger(__name__)


def initialise_sentry():
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
    )
