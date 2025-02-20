from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import resolve_url
from django.views.generic import DetailView

from jobserver.authorization import has_permission, permissions
from jobserver.reports import process_html

from .models import AnalysisRequest


class AnalysisRequestDetail(DetailView):
    context_object_name = "analysis_request"
    model = AnalysisRequest
    template_name = "interactive/analysis_request_detail.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.report and self.object.report.is_published:
            return self.render_to_response(
                context=self.get_context_data(object=self.object)
            )

        # mirror Django's login_required functionality since we can't decorate
        # the function, but we still want to redirect the user to log in such
        # that they can get back to this view
        if not request.user.is_authenticated:
            path = request.build_absolute_uri()
            resolved_login_url = resolve_url(settings.LOGIN_URL)
            # If the login url is the same scheme and net location then just
            # use the path as the "next" url.
            login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
            current_scheme, current_netloc = urlparse(path)[:2]
            if (not login_scheme or login_scheme == current_scheme) and (
                not login_netloc or login_netloc == current_netloc
            ):
                path = request.get_full_path()
            return redirect_to_login(path, resolved_login_url)

        if not has_permission(
            request.user, permissions.release_file_view, project=self.object.project
        ):
            raise PermissionDenied

        return self.render_to_response(
            context=self.get_context_data(object=self.object)
        )

    def get_context_data(self, **kwargs):
        report = process_html(self.object.report_content)
        return super().get_context_data(**kwargs) | {
            "report": report,
        }
