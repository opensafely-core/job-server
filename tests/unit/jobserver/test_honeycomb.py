from urllib.parse import unquote

import pytest
from django.utils import timezone

from jobserver.honeycomb import (
    format_honeycomb_timestamps,
    format_jobrequest_concurrency_link,
    format_trace_id,
    format_trace_link,
)

from ...factories import JobFactory, JobRequestFactory


def test_format_trace_id_hexadecimal():
    decimal_trace_id = 300559129712114075302075132513478005344
    hex_trace_id = "e21d953231b76bd98bf45d5e5bc85260"
    assert format_trace_id(decimal_trace_id) == hex_trace_id


def test_format_trace_id_hexadecimal_leading_zeros():
    decimal_trace_id = 15209551489903251743569348292329094282
    hex_trace_id = "0b7140c8e6bafc8ae485e68146dc3c8a"
    assert format_trace_id(decimal_trace_id) == hex_trace_id


@pytest.mark.freeze_time("2022-06-15 13:00")
def test_format_honeycomb_timestamps():
    job = JobFactory(completed_at=timezone.now())
    honeycomb_timestamps = format_honeycomb_timestamps(job)
    assert honeycomb_timestamps["honeycomb_starttime_unix"] == 1655297940
    assert honeycomb_timestamps["honeycomb_endtime_unix"] == 1655298060


@pytest.mark.freeze_time("2022-06-15 13:00")
def test_format_trace_link():
    job = JobFactory(completed_at=timezone.now())
    url = format_trace_link(job)
    assert "trace_start_ts=1655297940&trace_end_ts=1655298060" in url
    assert "bennett-institute-for-applied-data-science" in url


@pytest.mark.freeze_time("2022-10-12 17:00")
def test_format_jobrequest_concurrency_link():
    job_request = JobRequestFactory(identifier="jpbaeldzjqqiaolg")

    url = format_jobrequest_concurrency_link(job_request)
    expected_url = "https://ui.honeycomb.io/bennett-institute-for-applied-data-science/environments/production/datasets/jobrunner?query=%7B%22start_time%22%3A1665593940%2C%22end_time%22%3A1665594000%2C%22granularity%22%3A0%2C%22breakdowns%22%3A%5B%22name%22%5D%2C%22calculations%22%3A%5B%7B%22op%22%3A%22CONCURRENCY%22%7D%5D%2C%22filters%22%3A%5B%7B%22column%22%3A%22enter_state%22%2C%22op%22%3A%22!%3D%22%2C%22value%22%3A%22true%22%7D%2C%7B%22column%22%3A%22name%22%2C%22op%22%3A%22!%3D%22%2C%22value%22%3A%22RUN%22%7D%2C%7B%22column%22%3A%22name%22%2C%22op%22%3A%22!%3D%22%2C%22value%22%3A%22JOB%22%7D%2C%7B%22column%22%3A%22name%22%2C%22op%22%3A%22!%3D%22%2C%22value%22%3A%22job%22%7D%2C%7B%22column%22%3A%22job_request%22%2C%22op%22%3A%22%3D%22%2C%22value%22%3A%22jpbaeldzjqqiaolg%22%7D%5D%2C%22filter_combination%22%3A%22AND%22%2C%22orders%22%3A%5B%7B%22op%22%3A%22CONCURRENCY%22%2C%22order%22%3A%22descending%22%7D%5D%2C%22havings%22%3A%5B%5D%2C%22limit%22%3A1000%7D"

    assert unquote(url) == unquote(expected_url)
