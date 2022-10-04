from django.views.generic import TemplateView


class DashboardIndex(TemplateView):
    template_name = "staff/dashboards/index.html"
