from datetime import datetime

import pytest
from django.utils import timezone

from jobserver.models import Backend

from ...factories import StatsFactory


@pytest.mark.django_db
def test_stats_str_with_last_seen(freezer):
    tpp = Backend.objects.get(slug="tpp")

    last_seen = datetime(2020, 12, 25, 10, 11, 12, tzinfo=timezone.utc)
    stats = StatsFactory(backend=tpp, api_last_seen=last_seen, url="/foo")

    assert str(stats) == "tpp | 2020-12-25 10:11:12 | /foo"


@pytest.mark.django_db
def test_stats_str_without_last_seen(freezer):
    tpp = Backend.objects.get(slug="tpp")

    stats = StatsFactory(backend=tpp, api_last_seen=None, url="")

    assert str(stats) == "tpp | never | "
