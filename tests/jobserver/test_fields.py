import pytest
from django.db import connection

from jobserver.authorization import CoreDeveloper, OutputChecker, ProjectCollaborator
from jobserver.fields import RolesField, _ensure_role_paths, parse_roles

from ..factories import UserFactory


def test_ensure_role_paths_success():
    paths = [
        "jobserver.authorization.roles.OutputChecker",
        "jobserver.authorization.roles.ProjectCollaborator",
    ]

    assert _ensure_role_paths(paths) is None


def test_ensure_role_paths_with_invalid_paths():
    paths = [
        "jobserver.authorization.roles.OutputChecker",
        "test.dummy.SomeRole",
    ]

    msg = "Some Role paths did not start with jobserver.authorization.roles:\n"
    msg += " - test.dummy.SomeRole"
    with pytest.raises(ValueError, match=msg):
        _ensure_role_paths(paths)


def test_parse_roles_success():
    paths = [
        "jobserver.authorization.roles.OutputChecker",
        "jobserver.authorization.roles.ProjectCollaborator",
    ]

    roles = parse_roles(paths)

    assert roles == [OutputChecker, ProjectCollaborator]


@pytest.mark.django_db
def test_roles_field_db_values():
    user = UserFactory(roles=[CoreDeveloper])

    with connection.cursor() as c:
        c.execute("SELECT roles FROM jobserver_user WHERE id = %s", [user.pk])
        row = c.fetchone()

    assert row[0] == '["jobserver.authorization.roles.CoreDeveloper"]'


@pytest.mark.django_db
def test_roles_field_default_empty_list():
    # check default=list holds true
    assert UserFactory().roles == []


@pytest.mark.django_db
def test_roles_field_empty():
    user = UserFactory()

    assert user.roles == []

    user.save()
    user.refresh_from_db()

    assert user.roles == []


@pytest.mark.django_db
def test_roles_field_list_append():
    user = UserFactory()

    user.roles.append(CoreDeveloper)
    user.save()
    user.refresh_from_db()

    assert user.roles == [CoreDeveloper]


@pytest.mark.django_db
def test_roles_field_list_extend():
    user = UserFactory()

    user.roles.extend([CoreDeveloper])
    user.save()
    user.refresh_from_db()

    assert user.roles == [CoreDeveloper]


@pytest.mark.django_db
def test_roles_field_multiple_roles():
    user = UserFactory()

    user.roles = [CoreDeveloper, CoreDeveloper]
    user.save()
    user.refresh_from_db()

    assert user.roles == [CoreDeveloper]


@pytest.mark.django_db
def test_roles_field_one_role():
    user = UserFactory()

    user.roles = [CoreDeveloper]
    user.save()
    user.refresh_from_db()

    assert user.roles == [CoreDeveloper]


@pytest.mark.django_db
def test_roles_field_to_python_success():
    roles = RolesField()

    output = roles.to_python(["jobserver.authorization.roles.CoreDeveloper"])
    expected = [CoreDeveloper]

    assert output == expected


@pytest.mark.django_db
def test_roles_field_to_python_with_a_role():
    assert RolesField().to_python([CoreDeveloper]) == [CoreDeveloper]


@pytest.mark.django_db
def test_roles_field_to_python_with_empty_list():
    assert RolesField().to_python([]) == []


@pytest.mark.django_db
def test_roles_field_to_python_with_falsey_value():
    assert RolesField().to_python(None) is None
    assert RolesField().to_python([]) == []
