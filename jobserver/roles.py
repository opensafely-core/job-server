from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .github import is_member_of_org


def can_run_jobs(user):
    """
    Given User can run Jobs on the platform

    This is a short term (🤞) hack-adjacent way to enable our demo workflow
    before we can introduce proper role support (blocked by onboarding not
    having been built yet), and drive GitHub Org membership from job-server.
    """
    if not user.is_authenticated:
        return False

    return is_member_of_org("opensafely", user.username)


def superuser_required(f):
    """
    Decorator for views which require a Superuser

    User.is_superuser implies the User is authenticated.
    """

    @wraps(f)
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return f(request, *args, **kwargs)

        messages.error(request, "Only admins can view Backends.")
        return redirect("/")

    return wrapper
