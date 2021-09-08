from django.db import connection

from jobserver.authorization import CoreDeveloper, OutputChecker
from jobserver.authorization.fields import ExtractRoles, RolesField
from jobserver.models import User

from ....factories import UserFactory


def test_extractroles():
    user1 = UserFactory(roles=[OutputChecker])
    user2 = UserFactory(roles=[CoreDeveloper])

    users = User.objects.alias(extracted=ExtractRoles("roles")).filter(
        extracted__contains="CoreDeveloper"
    )

    assert len(users) == 1
    assert user1 not in users
    assert user2 in users


def test_roles_field_db_values():
    user = UserFactory(roles=[CoreDeveloper])

    with connection.cursor() as c:
        c.execute("SELECT roles FROM jobserver_user WHERE id = %s", [user.pk])
        row = c.fetchone()

    assert row[0] == '["jobserver.authorization.roles.CoreDeveloper"]'


def test_roles_field_default_empty_list():
    # check default=list holds true
    assert UserFactory().roles == []


def test_roles_field_empty():
    user = UserFactory()

    assert user.roles == []

    user.save()
    user.refresh_from_db()

    assert user.roles == []


def test_roles_field_list_append():
    user = UserFactory()

    user.roles.append(CoreDeveloper)
    user.save()
    user.refresh_from_db()

    assert user.roles == [CoreDeveloper]


def test_roles_field_list_extend():
    user = UserFactory()

    user.roles.extend([CoreDeveloper])
    user.save()
    user.refresh_from_db()

    assert user.roles == [CoreDeveloper]


def test_roles_field_multiple_roles():
    user = UserFactory()

    user.roles = [CoreDeveloper, CoreDeveloper]
    user.save()
    user.refresh_from_db()

    assert user.roles == [CoreDeveloper]


def test_roles_field_one_role():
    user = UserFactory()

    user.roles = [CoreDeveloper]
    user.save()
    user.refresh_from_db()

    assert user.roles == [CoreDeveloper]


def test_roles_field_to_python_success():
    roles = RolesField()

    output = roles.to_python(["jobserver.authorization.roles.CoreDeveloper"])
    expected = [CoreDeveloper]

    assert output == expected


def test_roles_field_to_python_with_a_role():
    assert RolesField().to_python([CoreDeveloper]) == [CoreDeveloper]


def test_roles_field_to_python_with_empty_list():
    assert RolesField().to_python([]) == []


def test_roles_field_to_python_with_falsey_value():
    assert RolesField().to_python(None) is None
    assert RolesField().to_python([]) == []
