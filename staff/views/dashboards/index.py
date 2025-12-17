from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from jobserver.authorization.decorators import require_permission
from jobserver.authorization.permissions import staff_area_access


@method_decorator(require_permission(staff_area_access), name="dispatch")
class DashboardIndex(TemplateView):
    template_name = "staff/dashboards/index.html"
