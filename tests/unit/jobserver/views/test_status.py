import functools
import time
from datetime import datetime, timedelta

import pytest
from django.utils import timezone
from first import first

from jobserver.views.status import MaintenanceMode, PerBackendStatus, Status

from ....factories import BackendFactory, JobFactory, JobRequestFactory, StatsFactory
from ....utils import minutes_ago


dt = functools.partial(datetime, tzinfo=timezone.utc)


def test_dbavailability_in_db_maintenance(rf):
    backend = BackendFactory(
        slug="tpp",
        jobrunner_state={"mode": {"v": "db-maintenance", "ts": time.time()}},
    )

    request = rf.get("/")

    response = MaintenanceMode.as_view()(request, backend=backend.slug)

    assert response.status_code == 503


def test_dbavailability_non_tpp(rf):
    backend = BackendFactory(slug="test")

    request = rf.get("/")

    response = MaintenanceMode.as_view()(request, backend=backend.slug)

    assert response.status_code == 200


def test_dbavailability_out_of_db_maintenance(rf):
    backend = BackendFactory(slug="tpp")

    request = rf.get("/")

    response = MaintenanceMode.as_view()(request, backend=backend.slug)

    assert response.status_code == 200


@pytest.mark.freeze_time("2022-3-23")  # set a fixed time to work against
@pytest.mark.parametrize(
    "alert_timeout,last_seen,expected_status",
    [
        (timedelta(minutes=5), dt(2022, 3, 22), 503),
        (timedelta(days=42), dt(2022, 3, 16), 200),
    ],
    ids=["missing", "not_missing"],
)
def test_perbackendstatus(rf, freezer, alert_timeout, last_seen, expected_status):
    backend = BackendFactory(alert_timeout=alert_timeout)
    StatsFactory(backend=backend, api_last_seen=last_seen)

    request = rf.get("/")
    response = PerBackendStatus.as_view()(request, backend=backend.slug)

    assert response.status_code == expected_status


def test_perbackendstatus_not_checked_in(rf):
    backend = BackendFactory(alert_timeout=timedelta(days=1))

    request = rf.get("/")
    response = PerBackendStatus.as_view()(request, backend=backend.slug)

    assert response.status_code == 200


def test_status_healthy(rf):
    backend = BackendFactory()

    # acked, because JobFactory will implicitly create JobRequests
    JobFactory.create_batch(3, job_request__backend=backend)

    last_seen = minutes_ago(timezone.now(), 1)
    StatsFactory(backend=backend, api_last_seen=last_seen)

    request = rf.get("/")
    response = Status.as_view()(request)

    output = first(response.context_data["backends"])

    assert output["last_seen"] == last_seen
    assert output["queue"]["acked"] == 3
    assert output["queue"]["unacked"] == 0
    assert not output["show_warning"]


def test_status_no_last_seen(rf):
    BackendFactory()

    request = rf.get("/")
    response = Status.as_view()(request)

    output = first(response.context_data["backends"])
    assert output["last_seen"] is None
    assert not output["show_warning"]


def test_status_unacked_jobs_but_recent_api_contact(rf):
    backend = BackendFactory()

    last_seen = minutes_ago(timezone.now(), 1)
    StatsFactory(backend=backend, api_last_seen=last_seen)

    request = rf.get("/")
    response = Status.as_view()(request)

    output = first(response.context_data["backends"])

    assert output["last_seen"] == last_seen
    assert not output["show_warning"]


def test_status_unhealthy(rf):
    backend = BackendFactory()

    # acked, because JobFactory will implicitly create JobRequests
    JobFactory.create_batch(2, job_request__backend=backend)

    # unacked, because it has no Jobs
    JobRequestFactory(backend=backend)

    last_seen = minutes_ago(timezone.now(), 10)
    StatsFactory(backend=backend, api_last_seen=last_seen, url="foo")

    request = rf.get("/")
    response = Status.as_view()(request)

    output = first(response.context_data["backends"])
    assert output["last_seen"] == last_seen
    assert output["queue"]["acked"] == 2
    assert output["queue"]["unacked"] == 1
    assert output["show_warning"]
