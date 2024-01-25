from datetime import timedelta

import pytest
from django.utils import timezone

from jobserver.commands import users

from ....factories import (
    BackendMembershipFactory,
    UserFactory,
    UserSocialAuthFactory,
)


def test_user_validate_token_login_allowed():
    user = UserFactory()

    with pytest.raises(users.InvalidTokenUser):
        users.validate_token_login_allowed(user)

    UserSocialAuthFactory(user=user)

    with pytest.raises(users.InvalidTokenUser):
        users.validate_token_login_allowed(user)

    BackendMembershipFactory(user=user)

    users.validate_token_login_allowed(user)


def test_user_login_token_flow_success(token_login_user):
    token = users.generate_login_token(token_login_user)
    assert token_login_user.login_token is not None
    assert token_login_user.login_token_expires_at is not None
    user = users.validate_login_token(token_login_user.username, token)
    assert user.login_token is None
    assert user.login_token_expires_at is None


def test_user_validate_login_token_no_token(token_login_user):
    # neither
    with pytest.raises(users.BadLoginToken):
        users.validate_login_token(token_login_user.username, "token")

    # token but no expiry
    users.generate_login_token(token_login_user)
    token_login_user.login_token_expires_at = None

    with pytest.raises(users.BadLoginToken):
        users.validate_login_token(token_login_user.username, "token")

    # expiry but no token
    users.generate_login_token(token_login_user)
    token_login_user.login_token = None

    with pytest.raises(users.BadLoginToken):
        users.validate_login_token(token_login_user.username, "token")


def test_user_validate_login_token_expired(token_login_user):
    token = users.generate_login_token(token_login_user)
    token_login_user.login_token_expires_at = timezone.now() - timedelta(minutes=1)
    token_login_user.save()

    with pytest.raises(users.ExpiredLoginToken):
        users.validate_login_token(token_login_user.username, token)


def test_validate_login_token_ignore_whitespace(token_login_user):
    token = users.generate_login_token(token_login_user)
    whitespace_token = "  ".join(token) + " "
    users.validate_login_token(token_login_user.username, whitespace_token)


def test_user_validate_login_token_wrong(token_login_user):
    users.generate_login_token(token_login_user)

    with pytest.raises(users.BadLoginToken):
        users.validate_login_token(token_login_user.username, "bad token")
