import sentry_sdk
from django.template.response import TemplateResponse

from jobserver.authorization.decorators import require_permission
from jobserver.authorization.permissions import staff_area_access


@require_permission(staff_area_access)
def error(request):
    1 / 0


@require_permission(staff_area_access)
def index(request):
    return TemplateResponse(request, "staff/sentry/index.html")


@require_permission(staff_area_access)
def message(request):
    sentry_sdk.capture_message("testing")
    return TemplateResponse(request, "staff/sentry/message.html")
