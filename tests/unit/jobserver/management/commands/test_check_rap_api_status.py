from django.core.management import call_command

from jobserver.management.commands.check_rap_api_status import Command as cd
from tests.factories import (
    BackendFactory,
    StatsFactory,
)


TEST_RESPONSE_BODY = {
    "backends": [
        {
            "name": "test",
            "last_seen": None,
            "paused": {"status": "off", "since": "2025-08-12T14:33:57.413881Z"},
            "db_maintenance": {"status": "off", "since": None, "type": None},
        }
    ]
}


def test_command(monkeypatch, log_output):
    monkeypatch.setattr(
        "jobserver.rap_api.backend_status",
        lambda: TEST_RESPONSE_BODY,
    )

    call_command("check_rap_api_status")

    assert log_output.entries[0] == {
        "event": TEST_RESPONSE_BODY,
        "log_level": "info",
    }


def test_command_error(monkeypatch, log_output):
    def fake_backend_status():
        raise Exception("something went wrong")

    monkeypatch.setattr("jobserver.rap_api.backend_status", fake_backend_status)

    call_command("check_rap_api_status")

    assert "error" == log_output.entries[0]["log_level"]
    assert "something went wrong" in str(log_output.entries[0]["event"])


class TestUpdateBackendState:
    def test_update_backend_state_no_dict(self, api_rf, monkeypatch):
        # The API response dict technically isn't empty as it has the "backends" key. This would bypass earlier JSON validation.
        # This is important if something goes wrong in building the response structure in jobrunner
        backend = BackendFactory()
        empty_response = {"backends": None}

        monkeypatch.setattr(
            "jobserver.rap_api.backend_status",
            lambda: empty_response,
        )

        cd.update_backend_state(backend, api_rf.get("/test"))
        # ... so no stats entry should be created
        assert backend.stats.count() == 0

    def test_update_backend_state_no_timestamp(self, api_rf, monkeypatch):
        backend = BackendFactory()

        # use custom mock response instead of fixture so we're able to pass a None value
        monkeypatch.setattr(
            "jobserver.rap_api.backend_status",
            lambda: TEST_RESPONSE_BODY,
        )
        cd.update_backend_state(
            backend,
            api_rf.get(
                "/test",
            ),
        )
        backend.refresh_from_db()
        assert backend.rap_api_state == {
            "name": "test",
            "last_seen": None,
            "paused": {"status": "off", "since": "2025-08-12T14:33:57.413881Z"},
            "db_maintenance": {"status": "off", "since": None, "type": None},
        }
        # no stats entry should be created
        assert backend.stats.count() == 0

    def test_update_backend_state_existing_url(
        self, api_rf, patch_backend_status_api_call
    ):
        backend = BackendFactory()
        patch_backend_status_api_call(backend.name)
        cd.update_backend_state(
            backend,
            api_rf.get(
                "/test",
            ),
        )
        backend.refresh_from_db()
        assert backend.rap_api_state == {
            "name": backend.name,
            "last_seen": "2025-08-12T06:57:43.039078Z",
            "paused": {"status": "off", "since": "2025-08-12T14:33:57.413881Z"},
            "db_maintenance": {"status": "off", "since": None, "type": None},
        }
        # check there's only one Stats for backend
        assert backend.stats.count() == 1
        assert backend.stats.first().url == "/test"

    def test_update_backend_state_new_url(self, api_rf, patch_backend_status_api_call):
        backend = BackendFactory()
        StatsFactory(backend=backend, url="/test")
        patch_backend_status_api_call(backend.name)
        cd.update_backend_state(
            backend,
            api_rf.get(
                "/new-url",
            ),
        )

        # check there are now two Stats for backend
        assert backend.stats.count() == 2
        assert backend.stats.last().url == "/new-url"
