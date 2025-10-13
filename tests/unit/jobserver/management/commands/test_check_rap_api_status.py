from datetime import datetime

import pytest
from django.core.management import call_command

from tests.factories import (
    BackendFactory,
)


@pytest.fixture
def patch_backend_status_api_call(monkeypatch):
    """
    Fixture to patch rap_api.backend_status with a fake response. Use this to test that the
    database is updated with the backend status.

    """

    def _do_backend_status_patch(backend_slug, last_seen="2025-08-12T06:57:43.039078Z"):
        # Mock a backend status response. If last_seen is not passed, use the default timestamp

        TEST_RESPONSE_BODY = {
            "backends": [
                {
                    "slug": f"{backend_slug}",
                    "last_seen": last_seen,
                    "paused": {
                        "status": "off",
                        "since": "2025-08-12T14:33:57.413881Z",
                    },
                    "db_maintenance": {
                        "status": "off",
                        "since": None,
                        "type": None,
                    },
                }
            ]
        }

        monkeypatch.setattr(
            "jobserver.rap_api.backend_status",
            lambda: TEST_RESPONSE_BODY,
        )
        return TEST_RESPONSE_BODY

    return _do_backend_status_patch


def test_command(log_output, patch_backend_status_api_call):
    backend = BackendFactory()

    test_response_body = patch_backend_status_api_call(backend.slug)

    call_command("check_rap_api_status")

    backend.refresh_from_db()

    log_output.entries[0].pop("timestamp")
    assert log_output.entries[0] == {
        "event": test_response_body,
        "log_level": "info",
        "level": "info",
        "logger": "jobserver.management.commands.check_rap_api_status",
    }


def test_command_error(monkeypatch, log_output):
    def fake_backend_status():
        raise Exception("something went wrong")

    monkeypatch.setattr("jobserver.rap_api.backend_status", fake_backend_status)

    call_command("check_rap_api_status")

    assert "error" == log_output.entries[0]["log_level"]
    assert "something went wrong" in str(log_output.entries[0]["event"])


def test_update_nonexistent_backend(patch_backend_status_api_call, log_output):
    patch_backend_status_api_call("other_backend")

    call_command("check_rap_api_status")

    assert "error" == log_output.entries[0]["log_level"]
    assert "does not exist" in str(log_output.entries[0]["event"])


def test_update_backend_state_no_timestamp(patch_backend_status_api_call):
    backend = BackendFactory()

    patch_backend_status_api_call(backend.slug, None)

    call_command("check_rap_api_status")

    backend.refresh_from_db()

    assert backend.rap_api_state == {
        "slug": backend.slug,
        "last_seen": None,
        "paused": {"status": "off", "since": "2025-08-12T14:33:57.413881Z"},
        "db_maintenance": {"status": "off", "since": None, "type": None},
    }
    # no stats entry should be created
    assert backend.stats.count() == 0


def test_update_backend_state_existing_url(patch_backend_status_api_call):
    backend = BackendFactory()
    patch_backend_status_api_call(backend.slug)

    call_command("check_rap_api_status")
    backend.refresh_from_db()

    assert backend.rap_api_state == {
        "slug": backend.slug,
        "last_seen": "2025-08-12T06:57:43.039078Z",
        "paused": {"status": "off", "since": "2025-08-12T14:33:57.413881Z"},
        "db_maintenance": {"status": "off", "since": None, "type": None},
    }
    # check there's only one Stats for backend
    assert backend.stats.count() == 1
    assert backend.stats.first().url == "http://example.com/rap/"


def test_update_backend_state_new_url(patch_backend_status_api_call, settings):
    backend = BackendFactory()

    patch_backend_status_api_call(backend.slug)
    call_command("check_rap_api_status")

    backend.refresh_from_db()

    assert backend.stats.count() == 1

    # patch a new url path using the settings fixture
    settings.RAP_API_BASE_URL = "http://example.com/rap/new"

    patch_backend_status_api_call(backend.slug)
    call_command("check_rap_api_status")

    backend.refresh_from_db()

    # check there are now two Stats for backend
    assert backend.stats.count() == 2
    assert backend.stats.last().url == "http://example.com/rap/new"


def test_update_backend_state_multiple_backends(monkeypatch):
    backend1 = BackendFactory()
    backend2 = BackendFactory()

    test_response_body = {
        "backends": [
            {
                "slug": f"{backend1.slug}",
                "last_seen": "2025-08-12T06:57:43.039078Z",
                "paused": {
                    "status": "off",
                    "since": "2025-08-12T14:33:57.413881Z",
                },
                "db_maintenance": {
                    "status": "off",
                    "since": None,
                    "type": None,
                },
            },
            {
                "slug": f"{backend2.slug}",
                "last_seen": "2025-08-12T06:57:43.039078Z",
                "paused": {
                    "status": "off",
                    "since": "2025-08-12T14:33:57.413881Z",
                },
                "db_maintenance": {
                    "status": "on",
                    "since": "2025-08-12T14:33:57.413881Z",
                    "type": "scheduled",
                },
            },
        ]
    }

    monkeypatch.setattr(
        "jobserver.rap_api.backend_status",
        lambda: test_response_body,
    )

    call_command("check_rap_api_status")

    backend1.refresh_from_db()

    assert backend1.rap_api_state == test_response_body["backends"][0]
    assert backend1.last_seen_at == datetime.fromisoformat(
        "2025-08-12T06:57:43.039078Z"
    )
    assert backend1.last_seen_maintenance_mode is None
    assert backend1.stats.count() == 1
    assert backend1.stats.first().url == "http://example.com/rap/"

    backend2.refresh_from_db()

    assert backend2.rap_api_state == test_response_body["backends"][1]
    assert backend2.last_seen_maintenance_mode == datetime.fromisoformat(
        "2025-08-12T14:33:57.413881Z"
    )
    assert backend2.is_in_maintenance_mode
    assert backend2.stats.count() == 1
    assert backend2.stats.first().url == "http://example.com/rap/"
