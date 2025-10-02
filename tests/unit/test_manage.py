"""Tests of custom manage.py behaviour."""

import os
import sys
from unittest.mock import patch

import manage


def test_sentry_setting_removed_for_shell_command(monkeypatch):
    """Test that calling the shell command removes the Sentry setting, so the
    Sentry integration is not active when using the interactive shell."""
    monkeypatch.setenv("SENTRY_DSN", "https://example@dsn")
    monkeypatch.setattr(sys, "argv", ["manage.py", "shell"])

    with patch("django.core.management.execute_from_command_line") as mock_func:
        manage.main()

    assert "SENTRY_DSN" not in os.environ
    mock_func.assert_called_once_with(["manage.py", "shell"])


def test_sentry_setting_not_removed_for_other_command(monkeypatch):
    """Test that calling a non-shell command does not alter the Sentry setting."""
    monkeypatch.setenv("SENTRY_DSN", "https://example@dsn")
    monkeypatch.setattr(sys, "argv", ["manage.py", "other_command"])

    with patch("django.core.management.execute_from_command_line") as mock_func:
        manage.main()

    assert os.environ.get("SENTRY_DSN") == "https://example@dsn"
    mock_func.assert_called_once_with(["manage.py", "other_command"])


def test_no_sentry_setting_with_shell_command(monkeypatch):
    """Test that calling the shell command does not REQUIRE the Sentry setting
    to be set."""
    monkeypatch.setattr(sys, "argv", ["manage.py", "shell"])
    assert "SENTRY_DSN" not in os.environ

    with patch("django.core.management.execute_from_command_line") as mock_func:
        manage.main()

    assert "SENTRY_DSN" not in os.environ
    mock_func.assert_called_once_with(["manage.py", "shell"])
