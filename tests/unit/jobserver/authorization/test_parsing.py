import pytest

from jobserver.authorization import OutputChecker, ProjectCollaborator
from jobserver.authorization.parsing import _ensure_role_paths, parse_roles


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
