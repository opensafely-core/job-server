from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from xkcdpass import xkcd_password

from jobserver.emails import (
    send_token_login_generated_email,
    send_token_login_used_email,
)
from jobserver.models import User


WORDLIST = xkcd_password.generate_wordlist("eff-long")


class TokenLoginException(Exception):
    pass


class BadLoginToken(TokenLoginException):
    pass


class ExpiredLoginToken(TokenLoginException):
    pass


class InvalidTokenUser(TokenLoginException):
    pass


def strip_token(token):
    return token.strip().replace(" ", "")


def human_memorable_token(size=8):
    """Generate a 3 short english words from the eff-long list of words."""
    return xkcd_password.generate_xkcdpassword(WORDLIST, numwords=3)


def validate_token_login_allowed(user):
    # only github users can log in with token
    if not user.social_auth.exists():
        raise InvalidTokenUser(f"User {user.username} is not a github user")

    # need at least 1 backend
    if not user.backends.exists():
        raise InvalidTokenUser(
            f"User {user.username} does not have access to any backends"
        )


def generate_login_token(user):
    """Generate, set and return single use login token and expiry"""
    validate_token_login_allowed(user)
    token = human_memorable_token()
    user.login_token = make_password(strip_token(token))
    user.login_token_expires_at = timezone.now() + timedelta(hours=1)
    user.save(update_fields=["login_token_expires_at", "login_token"])
    send_token_login_generated_email(user)
    return token


def validate_login_token(username, token):
    """Validates the supplied username and token are valid.

    Returns the validated user object, or raises.
    """

    # user can be username or email
    user = User.objects.get(Q(email=username) | Q(username=username))

    validate_token_login_allowed(user)

    if not (user.login_token and user.login_token_expires_at):
        raise BadLoginToken(f"No login token set for {user.username}")

    if timezone.now() > user.login_token_expires_at:
        raise ExpiredLoginToken(f"Token for {user.username} has expired")

    if not check_password(strip_token(token), user.login_token):
        raise BadLoginToken(f"Token for {user.username} was invalid")

    # all good - consume this token
    user.login_token = user.login_token_expires_at = None
    user.save(update_fields=["login_token_expires_at", "login_token"])
    send_token_login_used_email(user)

    return user


@transaction.atomic()
def update_roles(*, user, by, roles):
    user.roles = roles
    user.save(update_fields=["roles"])
