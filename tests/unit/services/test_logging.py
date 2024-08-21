from datetime import datetime

from services.logging import timestamper


def test_timestamper_with_debug(monkeypatch, freezer):
    monkeypatch.setattr("services.logging.DEBUG", True)

    now = datetime.now()
    freezer.move_to(now)

    log = timestamper(None, None, {"event": "derp"})
    assert log == {"event": "derp", "timestamp": now.isoformat() + "Z"}


def test_timestamper_without_debug(monkeypatch):
    monkeypatch.setattr("services.logging.DEBUG", False)

    assert timestamper(None, None, {"event": "derp"}) == {"event": "derp"}
