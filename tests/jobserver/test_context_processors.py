from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from jobserver.context_processors import nav, site_stats

from ..factories import JobFactory, StatsFactory


def test_nav_jobs(rf):
    job_list_url = reverse("job-list")
    request = rf.get(job_list_url)

    output = nav(request)

    jobs = output["nav"][1]
    workspaces = output["nav"][0]

    assert workspaces["is_active"] is False
    assert jobs["is_active"] is True


def test_nav_workspaces(rf):
    workspace_list_url = reverse("workspace-list")
    request = rf.get(workspace_list_url)

    output = nav(request)

    jobs = output["nav"][1]
    workspaces = output["nav"][0]

    assert workspaces["is_active"] is True
    assert jobs["is_active"] is False


@pytest.mark.django_db
def test_sitestats_healthy():
    JobFactory.create_batch(3, started=True, completed_at=None)

    last_seen = timezone.now() - timedelta(minutes=1)
    StatsFactory(api_last_seen=last_seen)

    output = site_stats(None)

    assert output["site_stats"]["last_seen"] == last_seen.strftime("%Y-%m-%d %H:%M:%S")
    assert output["site_stats"]["queue"]["acked"] == 3
    assert output["site_stats"]["queue"]["unacked"] == 0
    assert not output["site_stats"]["show_warning"]


@pytest.mark.django_db
def test_sitestats_no_last_seen():
    JobFactory(started=False)

    output = site_stats(None)

    assert output["site_stats"]["last_seen"] == "never"
    assert not output["site_stats"]["show_warning"]


@pytest.mark.django_db
def test_sitestats_unacked_jobs_but_recent_api_contact():
    JobFactory(started=False)

    last_seen = timezone.now() - timedelta(minutes=1)
    StatsFactory(api_last_seen=last_seen)

    output = site_stats(None)

    assert output["site_stats"]["last_seen"] == last_seen.strftime("%Y-%m-%d %H:%M:%S")
    assert not output["site_stats"]["show_warning"]


@pytest.mark.django_db
def test_sitestats_unhealthy():
    JobFactory(started=False, completed_at=None)
    JobFactory(started=True, completed_at=None)
    JobFactory(started=True, completed_at=None)

    last_seen = timezone.now() - timedelta(minutes=10)
    StatsFactory(api_last_seen=last_seen)

    output = site_stats(None)

    assert output["site_stats"]["last_seen"] == last_seen.strftime("%Y-%m-%d %H:%M:%S")
    assert output["site_stats"]["queue"]["acked"] == 2
    assert output["site_stats"]["queue"]["unacked"] == 1
    assert output["site_stats"]["show_warning"]
