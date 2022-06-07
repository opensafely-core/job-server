from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from jobserver.models import Backend


def get_backend_from_token(token):
    """
    Token based authentication.

    DRF's authentication framework is tied to the concept of a User making
    requests and, sensibly, assumes you will populate request.user on
    successful authentication with the appropriate User instance.  However,
    we want to authenticate each Backend without mixing them up with our
    Human Users, so per-user auth doesn't make sense.  This function handles
    token-based auth and returns the relevant Backend on success.

    Clients should authenticate by passing their token in the
    "Authorization" HTTP header.  For example:

        Authorization: 401f7ac837da42b97f613d789819ff93537bee6a

    """

    if token is None:
        raise NotAuthenticated("Authorization header is missing")

    if token == "":
        raise NotAuthenticated("Authorization header is empty")

    try:
        return Backend.objects.get(auth_token=token)
    except Backend.DoesNotExist:
        raise NotAuthenticated("Invalid token")


class NoAuthentication(BaseAuthentication):
    """Prevent authentication"""

    def authenticate(self, request):
        raise PermissionDenied("authentication is not allowed by default")
