import structlog
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, View
from furl import furl
from opentelemetry import trace
from social_django.utils import load_strategy

from jobserver.actions import users

from ..forms import RequireNameForm, SettingsForm
from ..models import JobRequest, User
from ..utils import is_safe_path


logger = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)


def get_next_url(request):
    next_url = request.GET.get("next") or "/"
    if not is_safe_path(next_url):
        next_url = ""

    f = furl(next_url)
    f.args.update(request.GET)

    # drop the next arg if we have one
    f.args.pop("next", None)

    return f.url


class Login(View):
    template_name = "login.html"

    def get(self, request, *args, **kwargs):
        self.next_url = get_next_url(self.request)

        if request.user.is_authenticated:
            return redirect(self.next_url)

        return TemplateResponse(
            request,
            "login.html",
            {
                "next_url": self.next_url,
            },
        )


class RequireName(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # logged in users are by design not using the pipeline
            return redirect("/")

        token = request.GET.get("partial_token")
        partial = load_strategy().partial_load(token)

        if partial is None:
            # we haven't arrived from the pipeline
            return redirect("/")

        context = {
            "form": RequireNameForm(),
            "partial": {
                "backend_name": partial.backend,
                "token": token,
            },
        }

        return TemplateResponse(request, "pipeline/require_name.html", context=context)


@method_decorator(login_required, name="dispatch")
class Settings(View):
    def get(self, request, *args, **kwargs):
        return self.render_to_response()

    def post(self, request, *args, **kwargs):
        # settings form
        if "settings" in request.POST:
            form = SettingsForm(request.POST)
            if not form.is_valid():
                messages.error(request, "Invalid settings")
                return self.render_to_response(form)

            request.user.fullname = form.cleaned_data["fullname"]
            request.user.email = form.cleaned_data["email"]
            request.user.save()
            messages.success(request, "Settings saved successfully")
            return self.render_to_response()

        # generate token form
        elif "token" in request.POST:
            try:
                users.validate_token_login_allowed(request.user)
            except users.InvalidTokenUser as e:
                logger.exception(
                    f"Refusing to generate login token for invalid user {request.user}"
                )
                trace.get_current_span().record_exception(e)
                messages.error(
                    request, "Your account is not allowed to generate a login token"
                )
                return self.render_to_response()

            token = users.generate_login_token(request.user)
            logger.info(f"User {request.user} generated a login token")
            return self.render_to_response(token=token)

        else:  # pragma: no cover
            messages.error(request, "Unrecognised form submission")
            return self.render_to_response()

    def render_to_response(self, form=None, token=None):
        if form is None:
            form = SettingsForm(
                data={
                    "fullname": self.request.user.fullname,
                    "email": self.request.user.email,
                }
            )

        try:
            users.validate_token_login_allowed(self.request.user)
            show_token_form = True
        except users.InvalidTokenUser:
            show_token_form = False

        context = {
            "form": form,
            "token": token,
            "show_token_form": show_token_form,
        }
        return TemplateResponse(self.request, "settings.html", context)


class UserDetail(DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"
    template_name = "user/detail.html"

    def get_context_data(self, **kwargs):
        projects = self.object.projects.order_by(Lower("name"))

        return super().get_context_data(**kwargs) | {
            "projects": projects,
        }


class UserEventLog(ListView):
    paginate_by = 25
    template_name = "user/event_log.html"

    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(User, username=self.kwargs["username"])

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "user": self.user,
        }

    def get_queryset(self):
        return (
            JobRequest.objects.with_started_at()
            .filter(created_by=self.user)
            .select_related("backend", "workspace", "workspace__project")
            .prefetch_related("workspace__project__orgs")
            .order_by("-pk")
        )


class UserList(ListView):
    model = User
    paginate_by = 25
    template_name = "user/list.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(project_count=Count("projects"))
            .order_by(*self.model._meta.ordering)
        )
