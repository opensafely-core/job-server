from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from jobserver.authorization.roles import (
    CoreDeveloper,
    InteractiveReporter,
    OrgCoordinator,
    OutputChecker,
    ProjectCollaborator,
    ProjectDeveloper,
)
from jobserver.models.user import User, get_or_create_user

from ....factories import (
    OrgFactory,
    OrgMembershipFactory,
    ProjectFactory,
    UserFactory,
)


def test_user_all_roles(project_membership):
    org = OrgFactory()
    project = ProjectFactory(orgs=[org])
    user = UserFactory(roles=[OutputChecker])

    OrgMembershipFactory(org=org, user=user, roles=[OutputChecker])
    project_membership(project=project, user=user, roles=[ProjectCollaborator])

    expected = {OutputChecker, ProjectCollaborator}

    assert user.all_roles == expected


def test_user_all_roles_empty():
    assert UserFactory().all_roles == set()


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


def test_user_get_absolute_url():
    user = UserFactory()

    url = user.get_absolute_url()

    assert url == reverse("user-detail", kwargs={"username": user.username})


def test_user_get_all_permissions(project_membership):
    org = OrgFactory()
    project = ProjectFactory(orgs=[org])
    user = UserFactory(roles=[CoreDeveloper])

    OrgMembershipFactory(org=org, user=user, roles=[OrgCoordinator])
    project_membership(project=project, user=user, roles=[ProjectDeveloper])

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


def test_user_get_all_roles(project_membership):
    project = ProjectFactory()
    user = UserFactory(roles=[OutputChecker])

    project_membership(project=project, user=user, roles=[ProjectCollaborator])

    output = user.get_all_roles()
    expected = {
        "global": ["OutputChecker"],
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


def test_user_get_staff_audit_url():
    user = UserFactory()

    url = user.get_staff_audit_url()

    assert url == reverse(
        "staff:user-audit-log",
        kwargs={
            "username": user.username,
        },
    )


def test_user_get_staff_clear_roles_url():
    user = UserFactory()

    url = user.get_staff_clear_roles_url()

    assert url == reverse(
        "staff:user-clear-roles",
        kwargs={
            "username": user.username,
        },
    )


def test_user_get_staff_roles_url():
    user = UserFactory()

    url = user.get_staff_roles_url()

    assert url == reverse(
        "staff:user-role-list",
        kwargs={
            "username": user.username,
        },
    )


def test_user_get_logs_url():
    user = UserFactory()

    url = user.get_logs_url()

    assert url == reverse("user-event-log", kwargs={"username": user.username})


def test_user_get_staff_url():
    user = UserFactory()

    url = user.get_staff_url()

    assert url == reverse(
        "staff:user-detail",
        kwargs={
            "username": user.username,
        },
    )


def test_user_initials_with_email():
    user = UserFactory(
        email="test@example.com", fullname="", username="test@example.com"
    )

    assert user.initials == "T"


@pytest.mark.parametrize(
    "name,initials",
    [
        ("Ben Goldacre", "BG"),
        ("Tom O'Dwyer", "TO"),
        ("Brian MacKenna", "BM"),
        ("Ben Butler-Cole", "BB"),
    ],
)
def test_user_initials_with_names(name, initials):
    assert UserFactory(fullname=name).initials == initials


def test_user_name():
    assert UserFactory(fullname="first last", username="test").name == "first last"
    assert UserFactory(username="username").name == "username"


def test_user_is_interactive_only(project_membership):
    # user ONLY has the InteractiveReporter role
    assert UserFactory(roles=[InteractiveReporter]).is_interactive_only

    user = UserFactory()
    project_membership(user=user, roles=[InteractiveReporter])
    assert user.is_interactive_only

    # user has the InteractiveReporter along with others
    assert not UserFactory(
        roles=[InteractiveReporter, ProjectDeveloper]
    ).is_interactive_only

    user = UserFactory()
    project_membership(user=user, roles=[InteractiveReporter, ProjectCollaborator])
    assert not user.is_interactive_only

    # user has no roles
    assert not UserFactory().is_interactive_only


def test_user_rotate_token(time_machine):
    user = UserFactory()

    assert user.pat_token is None
    assert user.pat_expires_at is None

    # shift time to a date in the past
    time_machine.move_to("2022-04-07")

    # set the user's pat_token and pat_expires_at
    token = user.rotate_token()

    # check the unhashed token has the pat_expires_at included
    assert token.endswith(user.pat_expires_at.date().isoformat())

    expires_at1 = user.pat_expires_at
    token1 = user.pat_token

    assert expires_at1
    assert token1

    # shift time forward a couple of days and update pat_* fields
    time_machine.move_to("2022-04-09")
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


def test_user_valid_pat_with_expired_token(time_machine):
    user = UserFactory()
    token = user.rotate_token()
    user.pat_expires_at = timezone.now() - timedelta(days=1)
    user.save()

    assert not user.has_valid_pat(token)


def test_user_valid_pat_with_invalid_token():
    user = UserFactory()
    user.rotate_token()

    assert not user.has_valid_pat("invalid")


def test_get_or_create_user_not_exists():
    user1, created = get_or_create_user("username", "email", "fullname")
    assert created
    assert User.objects.get(username="username") == user1
    user2, created = get_or_create_user("username", "email", "fullname")
    assert not created
    assert User.objects.get(username="username") == user2


@pytest.mark.parametrize(
    "update_fields",
    [
        {"email": "updated@example.com"},
        {"fullname": "updated"},
        {
            "email": "updated@example.com",
            "fullname": "updated",
        },
    ],
)
def test_get_or_create_user_update_fields(update_fields):
    user = UserFactory(
        username="username", email="original@example.com", fullname="original"
    )

    kwargs = {
        "username": "username",
        "email": user.email,
        "fullname": user.fullname,
        "update_fields": list(update_fields),
    }
    kwargs.update(**update_fields)

    expected_email = "updated" if "email" in update_fields else "original"
    expected_fullname = "updated" if "fullname" in update_fields else "original"

    user, created = get_or_create_user(**kwargs)
    assert not created
    assert user.email == expected_email + "@example.com"
    assert user.fullname == expected_fullname
