from datetime import timedelta

import structlog
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import FormView, UpdateView, View
from opentelemetry import trace

from jobserver.authorization import InteractiveReporter, has_role

from ..emails import send_github_login_email, send_login_email
from ..forms import EmailLoginForm
from ..models import User
from ..utils import is_safe_path


INTERNAL_LOGIN_SESSION_TOKEN = "_login_token"

logger = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class Login(FormView):
    form_class = EmailLoginForm
    template_name = "login.html"

    def dispatch(self, request, *args, **kwargs):
        self.next_url = self.get_next_url(request)

        if request.user.is_authenticated:
            return redirect(self.next_url)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = User.objects.filter(email=form.cleaned_data["email"]).first()

        if user:
            if not has_role(user, InteractiveReporter):
                messages.error(
                    self.request,
                    "Only users who have signed up to OpenSAFELY Interactive can log in via email",
                )
                return redirect("login")

            if user.social_auth.exists():
                # we don't want to expose users email address to a bad actor
                # via the login page form so we're emailing them with a link
                # to the login page to click the right button.
                # We can't email them with a link to the social auth entrypoint
                # because it only accepts POSTs.
                send_github_login_email(user)
            else:
                self.request.session[INTERNAL_LOGIN_SESSION_TOKEN] = user.email
                send_login_email(
                    user, timeout_minutes=settings.LOGIN_URL_TIMEOUT_MINUTES
                )

        msg = "If you have a user account we'll send you an email with the login details shortly. If you don't receive an email please check your spam folder."
        messages.success(self.request, msg)

        context = self.get_context_data(next_url=self.next_url)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "next_url": self.next_url,
        }

    def get_next_url(self, request):
        next_url = request.GET.get("next") or "/"
        if not is_safe_path(next_url):
            next_url = ""

        return next_url


class LoginWithURL(View):
    def get(self, request, *args, **kwargs):
        try:
            email = request.session.pop(INTERNAL_LOGIN_SESSION_TOKEN)
            TimestampSigner(salt="login").unsign(
                self.kwargs["token"],
                max_age=timedelta(minutes=settings.LOGIN_URL_TIMEOUT_MINUTES),
            )
            user = User.objects.get(email=email)
        except (BadSignature, KeyError, SignatureExpired, User.DoesNotExist) as e:
            logger.exception("Login failed")

            # also log to our metrics host
            span = trace.get_current_span()
            span.record_exception(e)

            msg = (
                "Invalid token, please try again. "
                "The link will only work in the same browser you requested the login email from."
            )
            messages.error(request, msg)
            return redirect("login")

        if not has_role(user, InteractiveReporter):
            messages.error(
                request,
                "Only users who have signed up to OpenSAFELY Interactive can log in via email",
            )
            return redirect("login")

        login(request, user, "django.contrib.auth.backends.ModelBackend")

        next_url = request.GET.get("next") or "/"
        return redirect(next_url)


@method_decorator(login_required, name="dispatch")
class Settings(UpdateView):
    fields = [
        "fullname",
        "notifications_email",
    ]
    template_name = "settings.html"

    def form_valid(self, form):
        response = super().form_valid(form)

        messages.success(self.request, "Settings saved successfully")

        return response

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return self.request.GET.get("next", "/")
