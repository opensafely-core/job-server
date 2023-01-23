import pytest
from django.utils import timezone

from jobserver import honeycomb
from jobserver.models import JobRequest

from ...factories import JobFactory, JobRequestFactory, WorkspaceFactory


def test_format_trace_id_hexadecimal():
    decimal_trace_id = 300559129712114075302075132513478005344
    hex_trace_id = "e21d953231b76bd98bf45d5e5bc85260"
    assert honeycomb.format_trace_id(decimal_trace_id) == hex_trace_id


def test_format_trace_id_hexadecimal_leading_zeros():
    decimal_trace_id = 15209551489903251743569348292329094282
    hex_trace_id = "0b7140c8e6bafc8ae485e68146dc3c8a"
    assert honeycomb.format_trace_id(decimal_trace_id) == hex_trace_id


@pytest.mark.freeze_time("2022-06-15 13:00")
def test_format_honeycomb_timestamps_job():
    job = JobFactory(completed_at=timezone.now(), status="succeeded")
    start, end = honeycomb.format_honeycomb_timestamps(job)
    assert start == 1655297940
    assert end == 1655298060


@pytest.mark.freeze_time("2022-06-15 13:00")
def test_format_honeycomb_timestamps_jobrequest():
    job_request = JobRequestFactory()
    job = JobFactory(  # noqa: F841
        job_request=job_request, completed_at=timezone.now(), status="succeeded"
    )
    prefetched_job_request = JobRequest.objects.filter(
        identifier=job_request.identifier
    ).first()

    start, end = honeycomb.format_honeycomb_timestamps(prefetched_job_request)
    assert start == 1655297940
    # 1 minute in the future
    assert end == 1655298060


@pytest.mark.freeze_time("2022-06-15 13:00")
def test_honeycomb_timestamps_jobrequest_unfinished():
    job_request = JobRequestFactory()
    job = JobFactory(job_request=job_request, status="executing")  # noqa: F841
    prefetched_job_request = JobRequest.objects.filter(
        identifier=job_request.identifier
    ).first()

    start, end = honeycomb.format_honeycomb_timestamps(prefetched_job_request)
    assert start == 1655297940
    # 1 day in the future
    assert end == 1655301600


@pytest.mark.freeze_time("2022-06-15 13:00")
def test_trace_link():
    job = JobFactory(completed_at=timezone.now())
    url = honeycomb.trace_link(job)
    assert "trace_start_ts=1655297940&trace_end_ts=1655298060" in url
    assert "bennett-institute-for-applied-data-science" in url


@pytest.mark.freeze_time("2022-10-12 17:00")
def test_status_link():
    job = JobFactory(completed_at=timezone.now(), identifier="test_identifier")
    url = honeycomb.status_link(job)
    parsed = honeycomb.TemplatedUrl.parse(url)

    assert parsed.stacked
    assert parsed.query == {
        "breakdowns": ["name"],
        "calculations": [
            {"op": "CONCURRENCY"},
            {"op": "AVG", "column": "cpu_percentage"},
            {"op": "AVG", "column": "memory_used"},
        ],
        "end_time": 1665594060,
        "filter_combination": "AND",
        "filters": [
            {"column": "scope", "op": "=", "value": "ticks"},
            {"column": "job", "op": "=", "value": "test_identifier"},
        ],
        "granularity": 0,
        "havings": [],
        "limit": 1000,
        "orders": [],
        "start_time": 1665593940,
    }


@pytest.mark.freeze_time("2022-10-12 17:00")
def test_jobrequest_link():
    job_request = JobRequestFactory(identifier="jpbaeldzjqqiaolg")
    job = JobFactory(  # noqa: F841
        job_request=job_request, completed_at=timezone.now(), status="succeeded"
    )
    prefetched_job_request = JobRequest.objects.filter(
        identifier=job_request.identifier
    ).first()

    url = honeycomb.jobrequest_link(prefetched_job_request)

    parsed = honeycomb.TemplatedUrl.parse(url)

    assert parsed.stacked
    assert parsed.query == {
        "breakdowns": ["name"],
        "calculations": [{"op": "CONCURRENCY"}],
        "end_time": 1665594060,
        "filter_combination": "AND",
        "filters": [
            {"column": "scope", "op": "=", "value": "jobs"},
            {"column": "enter_state", "op": "!=", "value": "true"},
            {"column": "name", "op": "!=", "value": "RUN"},
            {"column": "name", "op": "!=", "value": "JOB"},
            {"column": "name", "op": "!=", "value": "job"},
            {"column": "job_request", "op": "=", "value": "jpbaeldzjqqiaolg"},
        ],
        "granularity": 0,
        "havings": [],
        "limit": 1000,
        "orders": [{"op": "CONCURRENCY", "order": "descending"}],
        "start_time": 1665593940,
    }


@pytest.mark.freeze_time("2022-10-12 17:00")
def test_previous_actions_link():
    workspace = WorkspaceFactory(name="my_test_workspace")
    job_request = JobRequestFactory(identifier="jpbaeldzjqqiaolg", workspace=workspace)
    job = JobFactory(  # noqa: F841
        job_request=job_request,
        completed_at=timezone.now(),
        status="succeeded",
        action="my_sample_action",
    )

    url = honeycomb.previous_actions_link(job)
    parsed = honeycomb.TemplatedUrl.parse(url)

    assert parsed.query == {
        "breakdowns": [],
        "calculations": [{"column": "duration_minutes", "op": "HEATMAP"}],
        "filter_combination": "AND",
        "filters": [
            {"column": "scope", "op": "=", "value": "jobs"},
            {"column": "workspace", "op": "=", "value": "my_test_workspace"},
            {"column": "action", "op": "=", "value": "my_sample_action"},
            {"column": "name", "op": "=", "value": "EXECUTING"},
        ],
        "granularity": 0,
        "havings": [],
        "limit": 1000,
        "orders": [],
        "time_range": 2419200,
    }


@pytest.mark.freeze_time("2022-10-12 17:00")
def test_jobrequest_concurrency_link_unfinished():
    job_request = JobRequestFactory(identifier="jpbaeldzjqqiaolg")
    job = JobFactory(job_request=job_request, status="executing")  # noqa: F841
    prefetched_job_request = JobRequest.objects.filter(
        identifier=job_request.identifier
    ).first()

    url = honeycomb.jobrequest_link(prefetched_job_request)
    parsed = honeycomb.TemplatedUrl.parse(url)

    assert parsed.query["start_time"] == 1665593940
    assert parsed.query["end_time"] == 1665597600
