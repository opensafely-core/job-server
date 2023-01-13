from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetConfirmView
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.generic import FormView, UpdateView

from ..authorization import InteractiveReporter
from ..emails import send_github_login_email, send_reset_password_email
from ..forms import ResetPasswordForm
from ..models import User
from ..utils import is_safe_path


def login_view(request):
    next_url = request.GET.get("next") or "/"
    if not is_safe_path(next_url):
        next_url = ""

    if request.user.is_authenticated:
        return redirect(next_url)

    return TemplateResponse(request, "login.html", {"next_url": next_url})


class ResetPassword(FormView):
    form_class = ResetPasswordForm
    template_name = "reset_password.html"

    def form_valid(self, form):
        user = User.objects.filter(email=form.cleaned_data["email"]).first()

        # we have three possible states for the given email:
        # * unknown user
        # * GitHub user
        # * email-only user
        # we want to show the same outcome regardless of state so a bad actor
        # can't work out work out who uses the service by email
        if user:
            if user.social_auth.exists():
                # send GitHub users a link to the PSA entrypoint and explain
                # that they don't have a password to reset
                send_github_login_email(user)
            else:
                send_reset_password_email(user)

        messages.success(
            self.request, "Your password reset request was successfully sent."
        )
        return redirect("/")


class SetPassword(PasswordResetConfirmView):
    post_reset_login = True
    post_reset_login_backend = "django.contrib.auth.backends.ModelBackend"
    success_url = "/"
    template_name = "set_password.html"

    def get_success_url(self):
        # the authorization framework doesn't support getting all roles for a
        # user across all objects, so we hae to manually do it here.
        roles = set(self.request.user.roles)
        for membership in self.request.user.project_memberships.all():
            roles |= set(membership.roles)

        # treat users with only the InteractiveReporter role as interactive users.
        # we'll have users with this role along with others, eg for staff, but
        # they likely don't want to be redirected on login.
        if roles != {InteractiveReporter}:
            return "/"

        # if the user is logging in via this view, so with an email address and
        # password, _and_ has the InteractiveReporter role then they should
        # definitely be an interactive user.

        # TODO: add a page for users who have 2+ projects
        project = self.request.user.projects.first()
        return project.get_interactive_url()


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
