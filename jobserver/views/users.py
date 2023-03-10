import secrets
from datetime import timedelta

import structlog
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import FormView, UpdateView, View
from furl import furl
from opentelemetry import trace

from jobserver.authorization import InteractiveReporter

from ..emails import send_github_login_email, send_login_email
from ..forms import EmailLoginForm
from ..models import User
from ..utils import is_safe_path


INTERNAL_LOGIN_SESSION_TOKEN = "_login_token"

logger = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class BadToken(Exception):
    pass


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
            if user.social_auth.exists():
                # we don't want to expose users email address to a bad actor
                # via the login page form so we're emailing them with a link
                # to the login page to click the right button.
                # We can't email them with a link to the social auth entrypoint
                # because it only accepts POSTs.
                send_github_login_email(user)
            elif InteractiveReporter in user.all_roles:
                # generate a secret token we can sign for the URL
                token = secrets.token_urlsafe(64)
                signed_token = TimestampSigner(salt="login").sign(token)
                login_url = reverse("login-with-url", kwargs={"token": signed_token})

                # store the unsigned token and current user in the session so
                # we can check the token from the URL (after unsigning) is valid
                # when they try to use the URL, and also know which user to retrieve
                self.request.session[INTERNAL_LOGIN_SESSION_TOKEN] = (user.email, token)

                send_login_email(
                    user, login_url, timeout_minutes=settings.LOGIN_URL_TIMEOUT_MINUTES
                )

        msg = "If you have a user account we'll send you an email with the login details shortly. If you don't receive an email please check your spam folder."
        messages.success(self.request, msg)

        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "next_url": self.next_url,
        }

    def get_next_url(self, request):
        next_url = request.GET.get("next") or "/"
        if not is_safe_path(next_url):
            next_url = ""

        f = furl(next_url)
        f.args.update(request.GET)

        # drop the next arg if we have one
        f.args.pop("next", None)

        return f.url


class LoginWithURL(View):
    def get(self, request, *args, **kwargs):
        try:
            # get the requested user email and the expected token from the session
            # Note: we don't delete this until they successfully login since this
            # method is dependent on a user using the same browser so we want them to
            # be able to try again.
            email, token = request.session[INTERNAL_LOGIN_SESSION_TOKEN]
            url_token = TimestampSigner(salt="login").unsign(
                self.kwargs["token"],
                max_age=timedelta(minutes=settings.LOGIN_URL_TIMEOUT_MINUTES),
            )
            if url_token != token:
                raise BadToken

            user = User.objects.get(email=email)

            # now that we've successfully logged in we can remove the token
            del request.session[INTERNAL_LOGIN_SESSION_TOKEN]
        except (
            BadSignature,
            BadToken,
            KeyError,
            SignatureExpired,
            User.DoesNotExist,
        ) as e:
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

        if InteractiveReporter not in user.all_roles:
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
