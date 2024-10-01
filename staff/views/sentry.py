import sentry_sdk
from django.template.response import TemplateResponse

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role


@require_role(CoreDeveloper)
def error(request):
    1 / 0


@require_role(CoreDeveloper)
def index(request):
    return TemplateResponse(request, "staff/sentry/index.html")


@require_role(CoreDeveloper)
def message(request):
    sentry_sdk.capture_message("testing")
    return TemplateResponse(request, "staff/sentry/message.html")
