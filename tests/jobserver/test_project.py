from unittest.mock import patch

import pytest
from yaml.scanner import ScannerError

from jobserver.project import get_actions, get_project, load_yaml


dummy_project = {
    "version": "3.0",
    "expectations": {"population_size": 1000},
    "actions": {
        "generate_study_population": {
            "run": "cohortextractor:latest generate_cohort --study-definition study_definition",
            "outputs": {"highly_sensitive": {"cohort": "output/input.csv"}},
        },
        "run_model": {
            "run": "stata-mp:latest analysis/model.do",
            "needs": ["generate_study_population"],
            "outputs": {"moderately_sensitive": {"log": "logs/model.log"}},
        },
    },
}


def test_get_actions_empty_needs():
    dummy = {
        "actions": {
            "frobnicate": {
                "needs": None,
            }
        }
    }
    output = list(get_actions(dummy, {"frobnicate": "test"}))

    expected = [
        {"name": "frobnicate", "needs": [], "status": "test"},
        {"name": "run_all", "needs": ["frobnicate"], "status": "-"},
    ]
    assert output == expected


def test_get_actions_no_run_all():
    dummy = {
        "actions": {
            "frobnicate": {},
            "run_all": {
                "needs": ["frobnicate"],
            },
        }
    }

    action_status_lut = {
        "frobnicate": "running",
        "twiddle": "pending",
    }

    output = list(get_actions(dummy, action_status_lut))

    expected = [
        {"name": "frobnicate", "needs": [], "status": "running"},
        {"name": "run_all", "needs": ["frobnicate"], "status": "-"},
    ]
    assert output == expected


def test_get_actions_success():
    content = {
        "actions": {
            "frobnicate": {},
        }
    }
    output = list(get_actions(content, {"frobnicate": "test"}))

    expected = [
        {"name": "frobnicate", "needs": [], "status": "test"},
        {"name": "run_all", "needs": ["frobnicate"], "status": "-"},
    ]
    assert output == expected


def test_get_project_no_branch():
    with patch("jobserver.project.get_file", lambda r, b: None), patch(
        "jobserver.project.get_branch", lambda r, b: None
    ), pytest.raises(Exception, match="Missing branch: 'main'"):
        get_project("test", "main")


def test_get_project_no_project_yaml():
    with patch("jobserver.project.get_file", lambda r, b: None), patch(
        "jobserver.project.get_branch", lambda r, b: True
    ), pytest.raises(Exception, match="Could not find project.yaml"):
        get_project("test", "main")


def test_get_project_success():
    dummy = """
    actions:
      frobnicate:
    """
    with patch("jobserver.project.get_file", lambda r, b: dummy), patch(
        "jobserver.project.get_branch", lambda r, b: True
    ):
        assert get_project("test", "main") == dummy


def test_load_yaml_invalid_yaml():
    dummy_yaml = """
    <<<<<<< HEAD
    actions:
      frobnicate:
    """
    with pytest.raises(ScannerError):
        load_yaml(dummy_yaml)
