import pytest
from django.db import connection

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.fields import RolesField

from ...factories import OrgFactory, OrgMembershipFactory, UserFactory


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


@pytest.mark.django_db
def test_roles_field_with_invalid_role():
    org = OrgFactory()
    user = UserFactory()

    class ProjectRole:
        models = ["jobserver.models.ProjectMembership"]
        permissions = []

    msg = "Some roles could not be assigned to OrgMembership\n"
    msg += " - ProjectRole can only be assigned to these models:\n"
    msg += "   - jobserver.models.ProjectMembership"
    with pytest.raises(ValueError, match=msg):
        # This checks the RolesField on OrgMembership correctly identifies that
        # ProjectRole can't be assigned to it because it's models list defines
        # ProjectMembership as a valid Model.
        #
        # We're testing this with an OrgMembership (and thus its factory)
        # because RolesField makes use of the Model it's defined on to ensure
        # the passed Role is valid for that model so we can't call it directly.
        OrgMembershipFactory(org=org, user=user, roles=[ProjectRole])
