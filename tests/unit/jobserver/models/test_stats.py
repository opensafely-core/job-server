from datetime import UTC, datetime

from ....factories import BackendFactory, StatsFactory


def test_stats_str_with_last_seen(freezer):
    backend = BackendFactory(slug="test")

    last_seen = datetime(2020, 12, 25, 10, 11, 12, tzinfo=UTC)
    stats = StatsFactory(backend=backend, api_last_seen=last_seen, url="/foo")

    assert str(stats) == "test | 2020-12-25 10:11:12 | /foo"


def test_stats_str_without_last_seen(freezer):
    backend = BackendFactory(slug="test")

    stats = StatsFactory(backend=backend, api_last_seen=None, url="")

    assert str(stats) == "test | never | "
