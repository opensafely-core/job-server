from django.utils import timezone
from first import first

from jobserver.views.status import Status

from ....factories import BackendFactory, JobFactory, JobRequestFactory, StatsFactory
from ....utils import minutes_ago


def test_status_healthy(rf):
    backend = BackendFactory()

    # acked, because JobFactory will implicitly create JobRequests
    JobFactory.create_batch(3, job_request__backend=backend)

    last_seen = minutes_ago(timezone.now(), 1)
    StatsFactory(backend=backend, api_last_seen=last_seen)

    request = rf.get("/")
    response = Status.as_view()(request)

    output = first(response.context_data["backends"])

    assert output["last_seen"] == last_seen.strftime("%Y-%m-%d %H:%M:%S")
    assert output["queue"]["acked"] == 3
    assert output["queue"]["unacked"] == 0
    assert not output["show_warning"]


def test_status_no_last_seen(rf):
    BackendFactory()

    request = rf.get("/")
    response = Status.as_view()(request)

    output = first(response.context_data["backends"])
    assert output["last_seen"] == "never"
    assert not output["show_warning"]


def test_status_unacked_jobs_but_recent_api_contact(rf):
    backend = BackendFactory()

    last_seen = minutes_ago(timezone.now(), 1)
    StatsFactory(backend=backend, api_last_seen=last_seen)

    request = rf.get("/")
    response = Status.as_view()(request)

    output = first(response.context_data["backends"])

    assert output["last_seen"] == last_seen.strftime("%Y-%m-%d %H:%M:%S")
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
    assert output["last_seen"] == last_seen.strftime("%Y-%m-%d %H:%M:%S")
    assert output["queue"]["acked"] == 2
    assert output["queue"]["unacked"] == 1
    assert output["show_warning"]
