from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from jobserver.authorization.decorators import require_permission
from jobserver.authorization.permissions import Permission


@method_decorator(require_permission(Permission.STAFF_AREA_ACCESS), name="dispatch")
class DashboardIndex(TemplateView):
    template_name = "staff/dashboards/index.html"
