from unittest.mock import patch

import pytest
from yaml.scanner import ScannerError

from jobserver.project import get_actions


def test_get_actions_empty_needs():
    dummy_yaml = """
    actions:
      frobnicate:
        needs:
    """

    with patch("jobserver.project.get_file", lambda r, b: dummy_yaml):
        output = list(get_actions("test", "master", {"frobnicate": "test"}))

    expected = [
        {"name": "frobnicate", "needs": [], "status": "test"},
        {"name": "run_all", "needs": ["frobnicate"], "status": "-"},
    ]
    assert output == expected


def test_get_actions_no_project_yaml():
    with patch("jobserver.project.get_file", lambda r, b: None), pytest.raises(
        Exception, match="Could not find project.yaml"
    ):
        list(get_actions("test", "master", {}))


def test_get_actions_no_run_all():
    dummy_yaml = """
    actions:
      frobnicate:
      run_all:
        needs: [frobnicate]
    """

    action_status_lut = {
        "frobnicate": "running",
        "twiddle": "pending",
    }

    with patch("jobserver.project.get_file", lambda r, b: dummy_yaml):
        output = list(get_actions("test", "master", action_status_lut))

    expected = [
        {"name": "frobnicate", "needs": [], "status": "running"},
        {"name": "run_all", "needs": ["frobnicate"], "status": "-"},
    ]
    assert output == expected


def test_get_actions_invalid_yaml():
    dummy_yaml = """
    <<<<<<< HEAD
    actions:
      frobnicate:
    """

    with patch("jobserver.project.get_file", lambda r, b: dummy_yaml), pytest.raises(
        ScannerError
    ):
        list(get_actions("test", "master", {}))


def test_get_actions_success():
    dummy_yaml = """
    actions:
      frobnicate:
    """

    with patch("jobserver.project.get_file", lambda r, b: dummy_yaml):
        output = list(get_actions("test", "master", {"frobnicate": "test"}))

    expected = [
        {"name": "frobnicate", "needs": [], "status": "test"},
        {"name": "run_all", "needs": ["frobnicate"], "status": "-"},
    ]
    assert output == expected
