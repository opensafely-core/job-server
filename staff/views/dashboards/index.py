from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class DashboardIndex(TemplateView):
    template_name = "staff/dashboards/index.html"
