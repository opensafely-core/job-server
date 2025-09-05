from django.core.management import call_command


def test_command(monkeypatch, log_output):
    test_response_json = {
        "jobs": [
            {
                "identifier": "abc123",
                "rap_id": "abcdefgi12345678",
                "status": "succeeded",
            }
        ],
        "unrecognised_rap_ids": [],
    }
    test_log_output = "RAP: abcdefgi12345678 Job: abc123 Status: succeeded"

    monkeypatch.setattr(
        "jobserver.rap_api.status",
        lambda rap_ids: test_response_json,
    )

    call_command("rap_status", "abcdefgi12345678")

    assert log_output.entries[0] == {
        "event": test_log_output,
        "log_level": "info",
    }


def test_command_unrecognised(monkeypatch, log_output):
    test_response_json = {"jobs": [], "unrecognised_rap_ids": ["87654321ihgfedcba"]}
    test_log_output = "Unrecognised RAP id: 87654321ihgfedcba"

    monkeypatch.setattr(
        "jobserver.rap_api.status",
        lambda rap_ids: test_response_json,
    )

    call_command("rap_status", "87654321ihgfedcba")

    assert log_output.entries[0] == {
        "event": test_log_output,
        "log_level": "info",
    }


def test_command_error(monkeypatch, log_output):
    def fake_cancel(rap_ids):
        raise Exception("something went wrong")

    monkeypatch.setattr("jobserver.rap_api.status", fake_cancel)

    call_command("rap_status", "abcdefgi12345678")

    assert "error" == log_output.entries[0]["log_level"]
    assert "something went wrong" in str(log_output.entries[0]["event"])
