from jobserver.authorization import OutputChecker
from jobserver.utils import dotted_path


def test_dotted_path():
    assert dotted_path(OutputChecker) == "jobserver.authorization.roles.OutputChecker"
