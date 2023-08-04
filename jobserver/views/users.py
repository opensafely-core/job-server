import secrets
from datetime import timedelta

import structlog
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.db.models import Q
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import FormView, View
from furl import furl
from opentelemetry import trace
from social_django.utils import load_strategy

from jobserver.authorization import InteractiveReporter
from jobserver.emails import (
    send_token_login_generated_email,
    send_token_login_used_email,
)

from ..emails import send_github_login_email, send_login_email
from ..forms import EmailLoginForm, RequireNameForm, SettingsForm, TokenLoginForm
from ..models import User
from ..utils import is_safe_path


INTERNAL_LOGIN_SESSION_TOKEN = "_login_token"

logger = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class BadToken(Exception):
    pass


def get_next_url(request):
    next_url = request.GET.get("next") or "/"
    if not is_safe_path(next_url):
        next_url = ""

    f = furl(next_url)
    f.args.update(request.GET)

    # drop the next arg if we have one
    f.args.pop("next", None)

    return f.url


class Login(FormView):
    form_class = EmailLoginForm
    template_name = "login.html"

    def dispatch(self, request, *args, **kwargs):
        self.next_url = get_next_url(self.request)

        if request.user.is_authenticated:
            return redirect(self.next_url)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = User.objects.filter(email=form.cleaned_data["email"]).first()

        if user:
            if user.uses_social_auth:
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

        msg = (
            "If you have signed up to OpenSAFELY Interactive we'll send you an email with the login details shortly. "
            "If you don't receive an email please check your spam folder."
        )
        messages.success(self.request, msg)

        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "next_url": self.next_url,
            "token_form": TokenLoginForm(),
            "show_token_login": getattr(self.request, "backend", None) is not None,
        }


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
        except KeyError as e:
            # catch and hide missing session data.  This prevents us getting
            # Sentry errors for expected errors (eg a mail client prefetching
            # the login URL) but still notifies honeycomb so we can look for
            # rate changes.
            trace.get_current_span().record_exception(e)
            return self.login_invalid()
        except (BadSignature, BadToken, SignatureExpired, User.DoesNotExist) as e:
            # log and trace these exceptions to help us debug unexpected failures,
            # and in particular spikes in failure rate.  Sentry will also be
            # notified of these errors.
            logger.exception("Login via emailed url failed")
            trace.get_current_span().record_exception(e)  # also log to our metrics host

            return self.login_invalid()

        if InteractiveReporter not in user.all_roles:
            messages.error(
                request,
                "Only users who have signed up to OpenSAFELY Interactive can log in via email",
            )
            return redirect("login")

        login(request, user, "django.contrib.auth.backends.ModelBackend")

        if user.projects.count() > 1:
            return redirect("/")
        else:
            return redirect(user.projects.first().get_interactive_url())

    def login_invalid(self):
        msg = (
            "Invalid token, please try again. "
            "The link will only work in the same browser you requested the login email from."
        )
        messages.error(self.request, msg)
        return redirect("login")


class LoginWithToken(View):
    def post(self, request, *args, **kwargs):
        form = TokenLoginForm(request.POST)

        if getattr(request, "backend", None) is None:
            return self.login_invalid(form, "Token login only allowed from Level 4")

        if not form.is_valid():
            return self.login_invalid(form)

        user_value = form.cleaned_data["user"]

        try:
            # username or email
            user = User.objects.get(Q(email=user_value) | Q(username=user_value))

            user.validate_login_token(form.cleaned_data["token"])

        except (
            User.DoesNotExist,
            User.InvalidTokenUser,
            User.BadLoginToken,
            User.ExpiredLoginToken,
        ) as e:
            logger.info(f"Login with token failed for user {user_value}: {e}")
            trace.get_current_span().record_exception(e)
            return self.login_invalid(form)

        login(self.request, user, "django.contrib.auth.backends.ModelBackend")
        logger.info(f"User {user} logged in with login token")
        send_token_login_used_email(user)
        messages.success(
            self.request,
            "You have been logged in using a single use token. That token is now invalid.",
        )

        next_url = get_next_url(self.request)
        return redirect(next_url)

    def login_invalid(self, form, msg=None):
        if msg is None:
            msg = "Login failed. The user or token may be incorrect, or the token may have expired."
        messages.error(self.request, msg)

        return TemplateResponse(
            self.request,
            template="login.html",
            context={
                "token_form": form,
                "next_url": get_next_url(self.request),
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
                request.user.validate_token_login_allowed()
            except User.InvalidTokenUser as e:
                logger.exception(
                    f"Refusing to generate login token for invalid user {request.user}"
                )
                trace.get_current_span().record_exception(e)
                messages.error(
                    request, "Your account is not allowed to generate a login token"
                )
                return self.render_to_response()

            token = request.user.generate_login_token()
            logger.info(f"User {request.user} generated a login token")
            send_token_login_generated_email(request.user)
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
            self.request.user.validate_token_login_allowed()
            show_token_form = True
        except User.InvalidTokenUser:
            show_token_form = False

        context = {
            "form": form,
            "token": token,
            "show_token_form": show_token_form,
        }
        return TemplateResponse(self.request, "settings.html", context)
