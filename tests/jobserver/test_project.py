from unittest.mock import patch

from jobserver.project import get_actions


def test_get_actions_success():
    dummy_yaml = """
    actions:
      frobnicate:
    """

    with patch("jobserver.project.get_file", lambda r, b: dummy_yaml):
        output = dict(get_actions("test", "master"))

    assert output == {"frobnicate": {"needs": []}}
