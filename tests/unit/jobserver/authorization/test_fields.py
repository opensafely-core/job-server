from django.db import connection

from jobserver.authorization import StaffAreaAdministrator
from jobserver.authorization.fields import RoleField
from jobserver.models import User

from ....factories import UserFactory


def test_roles_field_db_values():
    user = UserFactory(roles=[StaffAreaAdministrator])

    with connection.cursor() as c:
        c.execute("SELECT roles FROM jobserver_user WHERE id = %s", [user.pk])
        row = c.fetchone()

    assert row[0] == ["jobserver.authorization.roles.StaffAreaAdministrator"]


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

    user.roles.append(StaffAreaAdministrator)
    user.save()
    user.refresh_from_db()

    assert user.roles == [StaffAreaAdministrator]


def test_roles_field_list_extend():
    user = UserFactory()

    user.roles.extend([StaffAreaAdministrator])
    user.save()
    user.refresh_from_db()

    assert user.roles == [StaffAreaAdministrator]


def test_roles_field_multiple_roles():
    user = UserFactory()

    user.roles = [StaffAreaAdministrator, StaffAreaAdministrator]
    user.save()
    user.refresh_from_db()

    assert user.roles == [StaffAreaAdministrator]


def test_roles_field_one_role():
    user = UserFactory()

    user.roles = [StaffAreaAdministrator]
    user.save()
    user.refresh_from_db()

    assert user.roles == [StaffAreaAdministrator]


def test_rolesarrayfield_to_python_success():
    roles = RoleField()

    output = roles.to_python("jobserver.authorization.roles.StaffAreaAdministrator")

    assert output == StaffAreaAdministrator


def test_roles_field_to_python_with_a_role():
    assert RoleField().to_python([StaffAreaAdministrator]) == [StaffAreaAdministrator]


def test_roles_field_to_python_with_empty_list():
    assert RoleField().to_python([]) == []


def test_roles_field_to_python_with_falsey_value():
    assert RoleField().to_python(None) is None
    assert RoleField().to_python([]) == []


def test_query_by_roles():
    user = UserFactory(roles=[StaffAreaAdministrator])

    qs = User.objects.filter(roles__contains=StaffAreaAdministrator)
    assert qs.count() == 1
    assert qs.first() == user

    assert not User.objects.filter(roles=[]).exists()
