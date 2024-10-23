from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from jobserver.authorization.roles import (
    InteractiveReporter,
    OutputChecker,
    ProjectCollaborator,
    ProjectDeveloper,
)
from jobserver.models.user import User

from ....factories import (
    OrgFactory,
    ProjectFactory,
    UserFactory,
)


def test_user_all_roles(project_membership):
    org = OrgFactory()
    project = ProjectFactory(orgs=[org])
    user = UserFactory(roles=[OutputChecker])

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


def test_user_get_all_permissions(role_factory, project_membership):
    org = OrgFactory()
    project = ProjectFactory(orgs=[org])
    user = UserFactory(roles=[role_factory(permission="a_global_permission")])

    project_membership(
        project=project,
        user=user,
        roles=[role_factory(permission="a_project_permission")],
    )

    output = user.get_all_permissions()
    expected = {
        "global": ["a_global_permission"],
        "projects": [{"slug": project.slug, "permissions": ["a_project_permission"]}],
    }

    assert output == expected


def test_user_get_all_permissions_empty():
    user = UserFactory()

    output = user.get_all_permissions()

    expected = {
        "global": [],
        "projects": [],
    }
    assert output == expected


def test_user_get_all_roles(project_membership):
    project = ProjectFactory()
    user = UserFactory(roles=[OutputChecker])

    project_membership(project=project, user=user, roles=[ProjectCollaborator])

    output = user.get_all_roles()
    expected = {
        "global": ["OutputChecker"],
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


def test_user_ordering():
    # Last due to empty fullname.
    user0 = UserFactory(fullname="", username="a")
    # Case-insensitive on username.
    user1 = UserFactory(fullname="", username="AA")
    # fullname has precedence over usename.
    user2 = UserFactory(fullname="alice", username="c")
    # Case-insensitive on fullname
    user3 = UserFactory(fullname="Charlie", username="e")
    user4 = UserFactory(fullname="bob", username="d")
    # fullname has precedence over username.
    user5 = UserFactory(fullname="Dino", username=" ")
    user6 = UserFactory(fullname="Alice", username="CC")

    users = User.objects.all()
    assert list(users) == [user2, user6, user4, user3, user5, user0, user1]


def test_create_user():
    """Test the UserManager.create manager method."""
    username = "Ⅳan"  # Note initial unicode character.
    email = "tEsT@TeSt.tEST"  # Note uppercase characters.
    password = "hunter2"
    user = User.objects.create(username=username, email=email, password=password)

    # Username unicode gets normalized.
    assert user.username == "IVan"
    # E-mail gets normalized by lower-casing.
    assert user.email == "test@test.test"
    # Password is not stored in plaintext.
    assert user.password != password
