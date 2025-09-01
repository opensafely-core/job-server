from django.core.management import call_command


_FAKE_ARGS = ("abcde1234", "action1", "action2")


def test_command(monkeypatch, log_output):
    test_response_body = b'{"foo": "bar"}'

    monkeypatch.setattr(
        "jobserver.rap_api.cancel",
        lambda rap_id, actions: test_response_body,
    )

    call_command("cancel_jobs", *_FAKE_ARGS)

    assert log_output.entries[0] == {
        "event": test_response_body,
        "log_level": "info",
    }


def test_command_error(monkeypatch, log_output):
    def fake_cancel(rap_id, actions):
        raise Exception("something went wrong")

    monkeypatch.setattr("jobserver.rap_api.cancel", fake_cancel)

    call_command("cancel_jobs", *_FAKE_ARGS)

    assert "error" == log_output.entries[0]["log_level"]
    assert "something went wrong" in str(log_output.entries[0]["event"])
