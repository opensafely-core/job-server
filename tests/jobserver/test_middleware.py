from datetime import timedelta

import pytest
from django.utils import timezone

from jobserver.middleware import stats_middleware
from jobserver.models import Stats

from ..factories import StatsFactory


@pytest.mark.django_db
def test_statsmiddleware_with_api_request(rf, freezer):
    StatsFactory(api_last_seen=timezone.now() - timedelta(minutes=30))
    assert Stats.objects.count() == 1

    request = rf.get("/api/test")
    stats_middleware(lambda r: r)(request)

    assert Stats.objects.count() == 1
    assert Stats.objects.first().api_last_seen == timezone.now()


@pytest.mark.django_db
def test_statsmiddleware_with_non_api_request(rf):
    thirty_minutes_ago = timezone.now() - timedelta(minutes=30)
    StatsFactory(api_last_seen=thirty_minutes_ago)

    request = rf.get("/api/test")
    stats_middleware(request)

    assert Stats.objects.first().api_last_seen == thirty_minutes_ago
