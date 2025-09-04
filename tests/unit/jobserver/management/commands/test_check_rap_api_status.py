from django.core.management import call_command


TEST_RESPONSE_BODY = b'{"backends":[{"name":"test","last_seen":"2025-08-12T06:57:43.039078Z","paused":{"status":"off","since":"2025-08-12T14:33:57.413881Z"},"db_maintenance":{"status":"off","since":null,"type":null}}]}'


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
