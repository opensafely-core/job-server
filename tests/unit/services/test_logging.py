from datetime import datetime

import pytest
from django.template import Context, Template

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


def test_missing_variable_error_filter():
    template = Template("*{{ my_missing_variable }}*", name="index.html")
    context = Context({"my_variable": "my_value"})

    with pytest.warns(UserWarning):
        template.render(context)


def test_missing_variable_error_filter_with_ignored_prefix():
    template = Template("*{{ my_missing_variable }}*", name="admin/index.html")
    context = Context({"my_variable": "my_value"})

    template.render(context) == "**"


def test_missing_variable_error_filter_with_ignored_variable_name():
    template = Template("*{{ csp_nonce }}*", name="index.html")
    context = Context({"csp_nonce": "csp_nonce_value"})

    template.render(context) == "*csp_nonce_value*"
