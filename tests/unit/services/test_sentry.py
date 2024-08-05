import json
import pathlib

import pytest

from services.sentry import monitor_config, parse


@pytest.fixture
def event():
    def loader(name="sentry_event.json"):
        path = pathlib.Path(__file__).parent.resolve() / name

        return json.load(path.open("r"))

    return loader


def test_monitor_config():
    schedule = "daily"
    config = monitor_config(schedule)
    assert config["schedule"]["value"] == f"@{schedule}"


def test_parse_with_envvar(monkeypatch, event):
    monkeypatch.setenv("INTERACTIVE_GITHUB_TOKEN", "ghp_testing")

    data = event()

    # confirm our test data is correct
    assert (
        "ghp_testing"
        in data["exception"]["values"][0]["stacktrace"]["frames"][0]["vars"]["analysis"]
    )

    output = parse(data)

    assert (
        "ghp_testing"
        not in output["exception"]["values"][0]["stacktrace"]["frames"][0]["vars"][
            "analysis"
        ]
    )


def test_parse_without_envvar(event):
    # confirm the function is a no-op when there's nothing to change

    data1 = event("sentry_event.json")
    data2 = event("sentry_event2.json")
    data3 = event("sentry_event_cron_in_progress.json")
    data4 = event("sentry_event_cron_error.json")

    assert parse(data1) == data1
    assert parse(data2) == data2
    assert parse(data3) == data3
    assert parse(data4) == data4
