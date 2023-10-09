from datetime import datetime

from services.logging import timestamper


def test_timestamper_with_debug(monkeypatch, time_machine):
    monkeypatch.setattr("services.logging.DEBUG", True)

    log = timestamper(None, None, {"event": "derp"})
    assert log == {"event": "derp", "timestamp": datetime.now().isoformat() + "Z"}


def test_timestamper_without_debug(monkeypatch):
    monkeypatch.setattr("services.logging.DEBUG", False)

    assert timestamper(None, None, {"event": "derp"}) == {"event": "derp"}
