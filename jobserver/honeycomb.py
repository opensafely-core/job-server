import json
from datetime import timedelta

from django.utils import timezone
from furl import furl


def honeycomb_furl():
    # TODO: make this configurable?
    return furl(
        "https://ui.honeycomb.io/bennett-institute-for-applied-data-science/environments/production/datasets/jobrunner"
    )


DEFAULT_QUERY = {
    "granularity": 0,
    "breakdowns": [],
    "calculations": [],
    "filters": [],
    "filter_combination": "AND",
    "orders": [],
    "havings": [],
    "limit": 1000,
}


class TemplatedUrl:
    def __init__(self, stacked=False, **kwargs):
        self.query = DEFAULT_QUERY.copy()
        self.query.update(kwargs)
        self.stacked = stacked

    @property
    def url(self):
        url = honeycomb_furl()
        url.add({"query": json.dumps(self.query, separators=(",", ":"))})
        if self.stacked:
            url.add({"useStackedGraphs": None})
        return url.url

    @classmethod
    def parse(cls, urlstring):
        parsed = furl(urlstring)
        query = json.loads(parsed.args["query"])
        url = cls(
            stacked="useStackedGraphs" in parsed.args,
            **query,
        )
        return url


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
    start_time = int((job_like.created_at - timedelta(minutes=1)).timestamp())

    end_time = timezone.now()

    if job_like.status not in ["failed", "succeeded"]:
        end_time = timezone.now() + timedelta(hours=1)

    if job_like.completed_at is not None:
        end_time = job_like.completed_at + timedelta(minutes=1)

    end_time = int(end_time.timestamp())

    return (start_time, end_time)


def trace_link(job):
    """Generate a url that links to the trace of a job in honeycomb"""
    # very old jobs won't have trace ids
    if not job.trace_id:  # pragma: no cover
        return None

    jobs_honeycomb_url = honeycomb_furl()
    trace_link = jobs_honeycomb_url / "trace"
    start, end = format_honeycomb_timestamps(job)
    trace_link.add(
        {
            "trace_id": format_trace_id(job.trace_id),
            "trace_start_ts": start,
            "trace_end_ts": end,
        }
    )
    return trace_link.url


def status_link(job):
    start, end = format_honeycomb_timestamps(job)
    url = TemplatedUrl(
        start_time=start,
        end_time=end,
        breakdowns=["name"],
        calculations=[{"op": "CONCURRENCY"}],
        orders=[{"op": "CONCURRENCY", "order": "descending"}],
        stacked=True,
        filters=[
            {"column": "scope", "op": "=", "value": "ticks"},
            {"column": "job", "op": "=", "value": job.identifier},
        ],
    )
    return url.url


def jobrequest_link(job_request):
    start, end = format_honeycomb_timestamps(job_request)
    url = TemplatedUrl(
        start_time=start,
        end_time=end,
        breakdowns=["name"],
        calculations=[{"op": "CONCURRENCY"}],
        orders=[{"op": "CONCURRENCY", "order": "descending"}],
        stacked=True,
        filters=[
            {"column": "scope", "op": "=", "value": "jobs"},
            {"column": "enter_state", "op": "!=", "value": "true"},
            {"column": "name", "op": "!=", "value": "RUN"},
            {"column": "name", "op": "!=", "value": "JOB"},
            {"column": "name", "op": "!=", "value": "job"},
            {"column": "job_request", "op": "=", "value": job_request.identifier},
        ],
    )
    return url.url


def previous_actions_link(job):
    # 28 days
    time_range_seconds = 2419200

    url = TemplatedUrl(
        time_range=time_range_seconds,
        calculations=[{"op": "HEATMAP", "column": "duration_minutes"}],
        filters=[
            {"column": "scope", "op": "=", "value": "jobs"},
            {"column": "workspace", "op": "=", "value": job.job_request.workspace.name},
            {"column": "action", "op": "=", "value": job.action},
            {"column": "name", "op": "=", "value": "EXECUTING"},
        ],
    )
    return url.url
