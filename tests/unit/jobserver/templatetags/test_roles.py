from jobserver.authorization import StaffAreaAdministrator
from jobserver.templatetags.roles import role_description


def test_role_description_success():
    output = role_description("jobserver.authorization.roles.StaffAreaAdministrator")

    assert output == StaffAreaAdministrator.description
