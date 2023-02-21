import json
import pathlib

import pytest

from services.sentry import parse


@pytest.fixture
def event():
    path = pathlib.Path(__file__).parent.resolve() / "sentry_event.json"

    return json.load(path.open("r"))


def test_parse(monkeypatch, event):
    monkeypatch.setenv("GITHUB_WRITEABLE_TOKEN", "ghp_testing")

    # confirm our test data is correct
    assert (
        "ghp_testing"
        in event["exception"]["values"][0]["stacktrace"]["frames"][0]["vars"][
            "analysis"
        ]
    )

    output = parse(event)

    assert (
        "ghp_testing"
        not in output["exception"]["values"][0]["stacktrace"]["frames"][0]["vars"][
            "analysis"
        ]
    )
