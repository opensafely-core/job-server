from jobserver.runtime import Runtime
from jobserver.templatetags.runtime import runtime


def test_runtime_no_runtime():
    assert runtime(None) == "-"


def test_runtime_success():
    r = Runtime(hours=1, minutes=37, seconds=12)

    assert runtime(r) == "01:37:12"
