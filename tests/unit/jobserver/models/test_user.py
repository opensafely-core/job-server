from datetime import timedelta

import pytest
from django.core.signing import TimestampSigner
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from jobserver.authorization.roles import (
    CoreDeveloper,
    DataInvestigator,
    OrgCoordinator,
    OutputChecker,
    OutputPublisher,
    ProjectCollaborator,
    ProjectDeveloper,
)
from jobserver.models import User

from ....factories import (
    OrgFactory,
    OrgMembershipFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    UserFactory,
)


def test_user_constraints_pat_token_and_pat_expires_at_both_set():
    UserFactory(pat_token="test", pat_expires_at=timezone.now())


def test_user_constraints_pat_token_and_pat_expires_at_neither_set():
    UserFactory(pat_token=None, pat_expires_at=None)


@pytest.mark.django_db(transaction=True)
def test_user_constraints_missing_pat_token_or_pat_expires_at():
    with pytest.raises(IntegrityError):
        UserFactory(pat_token=None, pat_expires_at=timezone.now())

    with pytest.raises(IntegrityError):
        UserFactory(pat_token="test", pat_expires_at=None)


def test_user_get_all_permissions():
    org = OrgFactory()
    project = ProjectFactory(org=org)
    user = UserFactory(roles=[CoreDeveloper])

    OrgMembershipFactory(org=org, user=user, roles=[OrgCoordinator])
    ProjectMembershipFactory(project=project, user=user, roles=[ProjectDeveloper])

    output = user.get_all_permissions()
    expected = {
        "global": [
            "application_manage",
            "backend_manage",
            "org_create",
            "user_manage",
        ],
        "orgs": [{"slug": org.slug, "permissions": []}],
        "projects": [
            {
                "slug": project.slug,
                "permissions": [
                    "job_cancel",
                    "job_run",
                    "snapshot_create",
                    "unreleased_outputs_view",
                    "workspace_archive",
                    "workspace_create",
                    "workspace_toggle_notifications",
                ],
            }
        ],
    }

    assert output == expected


def test_user_get_all_permissions_empty():
    user = UserFactory()

    output = user.get_all_permissions()

    expected = {
        "global": [],
        "projects": [],
        "orgs": [],
    }
    assert output == expected


def test_user_get_all_roles():
    project = ProjectFactory()
    user = UserFactory(roles=[DataInvestigator])

    ProjectMembershipFactory(project=project, user=user, roles=[ProjectCollaborator])

    output = user.get_all_roles()
    expected = {
        "global": ["DataInvestigator"],
        "orgs": [],
        "projects": [
            {
                "slug": project.slug,
                "roles": ["ProjectCollaborator"],
            }
        ],
    }

    assert output == expected


def test_user_get_all_roles_empty():
    user = UserFactory()

    output = user.get_all_roles()

    expected = {
        "global": [],
        "projects": [],
        "orgs": [],
    }
    assert output == expected


def test_user_get_login_url(mocker):
    user = UserFactory()

    class MockSecrets:
        def token_urlsafe(*args, **kwargs):
            return "test"

    mock_secrets = MockSecrets()

    mocker.patch("jobserver.models.core.secrets", new=mock_secrets)

    url = user.get_login_url()
    signed_token = TimestampSigner(salt="login").sign(mock_secrets.token_urlsafe())

    assert url == reverse(
        "login-with-url",
        kwargs={"token": signed_token},
    )


def test_user_get_staff_url():
    user = UserFactory()

    url = user.get_staff_url()

    assert url == reverse(
        "staff:user-detail",
        kwargs={
            "username": user.username,
        },
    )


def test_user_name():
    assert UserFactory(fullname="first last", username="test").name == "first last"
    assert UserFactory(username="username").name == "username"


def test_user_is_unapproved_by_default():
    assert not UserFactory().is_approved


def test_user_rotate_token(freezer):
    user = UserFactory()

    assert user.pat_token is None
    assert user.pat_expires_at is None

    # shift time to a date in the past
    freezer.move_to("2022-04-07")

    # set the user's pat_token and pat_expires_at
    token = user.rotate_token()

    # check the unhashed token has the pat_expires_at included
    assert token.endswith(user.pat_expires_at.date().isoformat())

    expires_at1 = user.pat_expires_at
    token1 = user.pat_token

    assert expires_at1
    assert token1

    # shift time forward a couple of days and update pat_* fields
    freezer.move_to("2022-04-09")
    user.rotate_token()

    assert user.pat_expires_at > expires_at1
    assert user.pat_token != token1


def test_user_valid_pat_success():
    user = UserFactory()
    token = user.rotate_token()

    assert user.has_valid_pat(token)


def test_user_valid_pat_with_empty_token():
    user = UserFactory()

    assert not user.has_valid_pat("")
    assert not user.has_valid_pat(None)


def test_user_valid_pat_with_expired_token(freezer):
    user = UserFactory()
    token = user.rotate_token()
    user.pat_expires_at = timezone.now() - timedelta(days=1)
    user.save()

    assert not user.has_valid_pat(token)


def test_user_valid_pat_with_invalid_token():
    user = UserFactory()
    user.rotate_token()

    assert not user.has_valid_pat("invalid")


def test_userqueryset_success():
    user1 = UserFactory(roles=[CoreDeveloper, OutputChecker])
    user2 = UserFactory(roles=[OutputChecker])
    user3 = UserFactory(roles=[OutputPublisher])

    users = User.objects.filter_by_role(OutputChecker)

    assert user1 in users
    assert user2 in users
    assert user3 not in users


def test_userqueryset_unknown_role():
    with pytest.raises(Exception, match="Unknown Roles:.*"):
        User.objects.filter_by_role("unknown")
