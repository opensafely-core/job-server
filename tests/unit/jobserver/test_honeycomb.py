from urllib.parse import unquote

import pytest
from django.utils import timezone

from jobserver.honeycomb import (
    format_honeycomb_timestamps,
    format_job_actions_link,
    format_jobrequest_concurrency_link,
    format_trace_id,
    format_trace_link,
)
from jobserver.models import JobRequest

from ...factories import JobFactory, JobRequestFactory, WorkspaceFactory


def test_format_trace_id_hexadecimal():
    decimal_trace_id = 300559129712114075302075132513478005344
    hex_trace_id = "e21d953231b76bd98bf45d5e5bc85260"
    assert format_trace_id(decimal_trace_id) == hex_trace_id


def test_format_trace_id_hexadecimal_leading_zeros():
    decimal_trace_id = 15209551489903251743569348292329094282
    hex_trace_id = "0b7140c8e6bafc8ae485e68146dc3c8a"
    assert format_trace_id(decimal_trace_id) == hex_trace_id


@pytest.mark.freeze_time("2022-06-15 13:00")
def test_format_honeycomb_timestamps_job():
    job = JobFactory(completed_at=timezone.now(), status="succeeded")
    honeycomb_timestamps = format_honeycomb_timestamps(job)
    assert honeycomb_timestamps["honeycomb_starttime_unix"] == 1655297940
    assert honeycomb_timestamps["honeycomb_endtime_unix"] == 1655298060


@pytest.mark.freeze_time("2022-06-15 13:00")
def test_format_honeycomb_timestamps_jobrequest():
    job_request = JobRequestFactory()
    job = JobFactory(  # noqa: F841
        job_request=job_request, completed_at=timezone.now(), status="succeeded"
    )
    prefetched_job_request = JobRequest.objects.filter(
        identifier=job_request.identifier
    ).first()

    honeycomb_timestamps = format_honeycomb_timestamps(prefetched_job_request)
    assert honeycomb_timestamps["honeycomb_starttime_unix"] == 1655297940
    # 1 minute in the future
    assert honeycomb_timestamps["honeycomb_endtime_unix"] == 1655298060


@pytest.mark.freeze_time("2022-06-15 13:00")
def test_format_honeycomb_timestamps_jobrequest_unfinished():
    job_request = JobRequestFactory()
    job = JobFactory(job_request=job_request, status="executing")  # noqa: F841
    prefetched_job_request = JobRequest.objects.filter(
        identifier=job_request.identifier
    ).first()

    honeycomb_timestamps = format_honeycomb_timestamps(prefetched_job_request)
    assert honeycomb_timestamps["honeycomb_starttime_unix"] == 1655297940
    # 1 day in the future
    assert honeycomb_timestamps["honeycomb_endtime_unix"] == 1655301600


@pytest.mark.freeze_time("2022-06-15 13:00")
def test_format_trace_link():
    job = JobFactory(completed_at=timezone.now())
    url = format_trace_link(job)
    assert "trace_start_ts=1655297940&trace_end_ts=1655298060" in url
    assert "bennett-institute-for-applied-data-science" in url


@pytest.mark.freeze_time("2022-10-12 17:00")
def test_format_jobrequest_concurrency_link():
    job_request = JobRequestFactory(identifier="jpbaeldzjqqiaolg")
    job = JobFactory(  # noqa: F841
        job_request=job_request, completed_at=timezone.now(), status="succeeded"
    )
    prefetched_job_request = JobRequest.objects.filter(
        identifier=job_request.identifier
    ).first()

    url = format_jobrequest_concurrency_link(prefetched_job_request)
    expected_url = "https://ui.honeycomb.io/bennett-institute-for-applied-data-science/environments/production/datasets/jobrunner?query=%7B%22start_time%22%3A1665593940%2C%22end_time%22%3A1665594060%2C%22granularity%22%3A0%2C%22breakdowns%22%3A%5B%22name%22%5D%2C%22calculations%22%3A%5B%7B%22op%22%3A%22CONCURRENCY%22%7D%5D%2C%22filters%22%3A%5B%7B%22column%22%3A%22enter_state%22%2C%22op%22%3A%22!%3D%22%2C%22value%22%3A%22true%22%7D%2C%7B%22column%22%3A%22name%22%2C%22op%22%3A%22!%3D%22%2C%22value%22%3A%22RUN%22%7D%2C%7B%22column%22%3A%22name%22%2C%22op%22%3A%22!%3D%22%2C%22value%22%3A%22JOB%22%7D%2C%7B%22column%22%3A%22name%22%2C%22op%22%3A%22!%3D%22%2C%22value%22%3A%22job%22%7D%2C%7B%22column%22%3A%22job_request%22%2C%22op%22%3A%22%3D%22%2C%22value%22%3A%22jpbaeldzjqqiaolg%22%7D%5D%2C%22filter_combination%22%3A%22AND%22%2C%22orders%22%3A%5B%7B%22op%22%3A%22CONCURRENCY%22%2C%22order%22%3A%22descending%22%7D%5D%2C%22havings%22%3A%5B%5D%2C%22limit%22%3A1000%7D&useStackedGraphs"

    assert "start_time%22%3A1665593940" in url
    assert "end_time%22%3A1665594060" in url
    assert "useStackedGraphs" in url
    assert unquote(url) == unquote(expected_url)


@pytest.mark.freeze_time("2022-10-12 17:00")
def test_format_job_actions_link():
    workspace = WorkspaceFactory(name="my_test_workspace")
    job_request = JobRequestFactory(identifier="jpbaeldzjqqiaolg", workspace=workspace)
    job = JobFactory(  # noqa: F841
        job_request=job_request,
        completed_at=timezone.now(),
        status="succeeded",
        action="my_sample_action",
    )

    url = format_job_actions_link(job)
    expected_url = "https://ui.honeycomb.io/bennett-institute-for-applied-data-science/environments/production/datasets/jobrunner?query=%7B%22time_range%22%3A2419200%2C%22granularity%22%3A0%2C%22breakdowns%22%3A%5B%5D%2C%22calculations%22%3A%5B%7B%22op%22%3A%22HEATMAP%22%2C%22column%22%3A%22duration_minutes%22%7D%5D%2C%22filters%22%3A%5B%7B%22column%22%3A%22workspace%22%2C%22op%22%3A%22%3D%22%2C%22value%22%3A%22my_test_workspace%22%7D%2C%7B%22column%22%3A%22action%22%2C%22op%22%3A%22%3D%22%2C%22value%22%3A%22my_sample_action%22%7D%2C%7B%22column%22%3A%22name%22%2C%22op%22%3A%22%3D%22%2C%22value%22%3A%22EXECUTING%22%7D%5D%2C%22filter_combination%22%3A%22AND%22%2C%22orders%22%3A%5B%5D%2C%22havings%22%3A%5B%5D%2C%22limit%22%3A1000%7D"

    assert "time_range%22%3A2419200" in url
    assert "start_time" not in url
    assert "end_time" not in url
    assert '"workspace","op":"=","value":"my_test_workspace"' in unquote(url)
    assert '"action","op":"=","value":"my_sample_action"' in unquote(url)
    assert unquote(url) == unquote(expected_url)


@pytest.mark.freeze_time("2022-10-12 17:00")
def test_format_jobrequest_concurrency_link_unfinished():
    job_request = JobRequestFactory(identifier="jpbaeldzjqqiaolg")
    job = JobFactory(job_request=job_request, status="executing")  # noqa: F841
    prefetched_job_request = JobRequest.objects.filter(
        identifier=job_request.identifier
    ).first()

    url = format_jobrequest_concurrency_link(prefetched_job_request)
    assert "start_time%22%3A1665593940" in url
    assert "end_time%22%3A1665597600" in url
