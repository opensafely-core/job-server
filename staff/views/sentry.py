import sentry_sdk
from django.template.response import TemplateResponse

from jobserver.authorization.decorators import require_permission
from jobserver.authorization.permissions import Permission


@require_permission(Permission.STAFF_AREA_ACCESS)
def error(request):
    1 / 0


@require_permission(Permission.STAFF_AREA_ACCESS)
def index(request):
    return TemplateResponse(request, "staff/sentry/index.html")


@require_permission(Permission.STAFF_AREA_ACCESS)
def message(request):
    sentry_sdk.capture_message("testing")
    return TemplateResponse(request, "staff/sentry/message.html")
