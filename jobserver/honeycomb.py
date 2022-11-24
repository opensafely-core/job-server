import json
from datetime import timedelta

from django.utils import timezone
from furl import furl


def format_trace_id(trace_id):
    """Format the trace_id for Honeycomb.
    Hexadecimal without the 0x prefix and with leading zeros.
    """
    return f"{trace_id:032x}"


def format_honeycomb_timestamps(job_like):
    """Return UNIX timestamps for the start and end of a job-like.
    Will accept a job or a job_request.
    """

    # Add arbitrary small timedeltas to the start and end times.
    # If we use the exact start and end times of a job, we do not
    # reliably see the first and last honeycomb events relating to that job.
    # This could be due to clock skew, '>' rather than '>=' comparators
    # and/or other factors.
    honeycomb_starttime_unix = int(
        (job_like.created_at - timedelta(minutes=1)).timestamp()
    )

    honeycomb_endtime = timezone.now()

    if job_like.status not in ["failed", "succeeded"]:
        honeycomb_endtime = timezone.now() + timedelta(hours=1)

    if job_like.completed_at is not None:
        honeycomb_endtime = job_like.completed_at + timedelta(minutes=1)

    honeycomb_endtime_unix = int(honeycomb_endtime.timestamp())
    return {
        "honeycomb_starttime_unix": honeycomb_starttime_unix,
        "honeycomb_endtime_unix": honeycomb_endtime_unix,
    }


def honeycomb_furl():
    # TODO: make this configurable?
    return furl(
        "https://ui.honeycomb.io/bennett-institute-for-applied-data-science/environments/production/datasets/jobrunner"
    )


def format_trace_link(job):
    """Generate a url that links to the trace of a job in honeycomb"""
    if not job.trace_id:
        return None

    jobs_honeycomb_url = honeycomb_furl()
    trace_link = jobs_honeycomb_url / "trace"
    honeycomb_timestamps = format_honeycomb_timestamps(job)
    trace_link.add(
        {
            "trace_id": format_trace_id(job.trace_id),
            "trace_start_ts": honeycomb_timestamps["honeycomb_starttime_unix"],
            "trace_end_ts": honeycomb_timestamps["honeycomb_endtime_unix"],
        }
    )
    return trace_link.url


def format_jobrequest_concurrency_link(job_request):
    jobs_honeycomb_url = honeycomb_furl()

    honeycomb_timestamps = format_honeycomb_timestamps(job_request)

    query_json = {
        "start_time": honeycomb_timestamps["honeycomb_starttime_unix"],
        "end_time": honeycomb_timestamps["honeycomb_endtime_unix"],
        "granularity": 0,
        "breakdowns": ["name"],
        "calculations": [{"op": "CONCURRENCY"}],
        "filters": [
            {"column": "enter_state", "op": "!=", "value": "true"},
            {"column": "name", "op": "!=", "value": "RUN"},
            {"column": "name", "op": "!=", "value": "JOB"},
            {"column": "name", "op": "!=", "value": "job"},
            {"column": "job_request", "op": "=", "value": job_request.identifier},
        ],
        "filter_combination": "AND",
        "orders": [{"op": "CONCURRENCY", "order": "descending"}],
        "havings": [],
        "limit": 1000,
    }

    jobs_honeycomb_url.add(
        {
            "query": json.dumps(query_json, separators=(",", ":")),
            "useStackedGraphs": None,
        }
    )

    return jobs_honeycomb_url.url


def format_job_actions_link(job):
    jobs_honeycomb_url = honeycomb_furl()

    # 28 days
    time_range_seconds = 2419200

    query_json = {
        "time_range": time_range_seconds,
        "granularity": 0,
        "breakdowns": [],
        "calculations": [{"op": "HEATMAP", "column": "duration_minutes"}],
        "filters": [
            {"column": "workspace", "op": "=", "value": job.job_request.workspace.name},
            {"column": "action", "op": "=", "value": job.action},
            {"column": "name", "op": "=", "value": "EXECUTING"},
            {"column": "tick", "op": "does-not-exist"},
        ],
        "filter_combination": "AND",
        "orders": [],
        "havings": [],
        "limit": 1000,
    }

    jobs_honeycomb_url.add({"query": json.dumps(query_json, separators=(",", ":"))})

    return jobs_honeycomb_url.url
