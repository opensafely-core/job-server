from jobserver.authorization import CoreDeveloper
from jobserver.templatetags.roles import role_description


def test_role_description_success():
    output = role_description("jobserver.authorization.roles.CoreDeveloper")

    assert output == CoreDeveloper.description
