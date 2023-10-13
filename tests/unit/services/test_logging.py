from datetime import datetime

from services.logging import timestamper


def test_timestamper_with_debug(monkeypatch, time_machine):
    monkeypatch.setattr("services.logging.DEBUG", True)

    now = datetime.now()
    time_machine.move_to(now, tick=False)

    log = timestamper(None, None, {"event": "derp"})
    assert log == {"event": "derp", "timestamp": now.isoformat() + "Z"}


def test_timestamper_without_debug(monkeypatch):
    monkeypatch.setattr("services.logging.DEBUG", False)

    assert timestamper(None, None, {"event": "derp"}) == {"event": "derp"}
