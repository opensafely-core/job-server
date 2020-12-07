from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from jobserver.context_processors import backend_warnings, nav

from ..factories import JobRequestFactory, StatsFactory


@pytest.mark.django_db
def test_backend_warnings_with_no_warnings(rf):
    last_seen = timezone.now() - timedelta(minutes=1)
    StatsFactory(api_last_seen=last_seen)

    request = rf.get("/")
    output = backend_warnings(request)

    assert output["backend_warnings"] == []


@pytest.mark.django_db
def test_backend_warnings_with_warnings(rf):
    JobRequestFactory()

    last_seen = timezone.now() - timedelta(minutes=10)
    StatsFactory(api_last_seen=last_seen)

    request = rf.get("/")
    output = backend_warnings(request)

    assert output["backend_warnings"] == ["TPP"]


def test_nav_jobs(rf):
    job_list_url = reverse("job-list")
    request = rf.get(job_list_url)

    output = nav(request)

    jobs = output["nav"][0]
    status = output["nav"][1]

    assert jobs["is_active"] is True
    assert status["is_active"] is False
