from datetime import timedelta

from django.utils import timezone
from furl import furl


def format_trace_id(trace_id):
    """Format the trace_id for Honeycomb.
    Hexadecimal without the 0x prefix and with leading zeros.
    """
    return f"{trace_id:032x}"


def format_honeycomb_timestamps(job):
    # Add arbitrary small timedeltas to the start and end times.
    # If we use the exact start and end times of a job, we do not
    # reliably see the first and last honeycomb events relating to that job.
    # This could be due to clock skew, '>' rather than '>=' comparators
    # and/or other factors.
    honeycomb_starttime_unix = int((job.created_at - timedelta(minutes=1)).timestamp())

    honeycomb_endtime = timezone.now()
    if job.completed_at is not None:
        honeycomb_endtime = job.completed_at + timedelta(minutes=1)

    honeycomb_endtime_unix = int(honeycomb_endtime.timestamp())
    return {
        "honeycomb_starttime_unix": honeycomb_starttime_unix,
        "honeycomb_endtime_unix": honeycomb_endtime_unix,
    }


def format_trace_link(job):
    """Generate a url that links to the trace of a job in honeycomb"""
    if not job.trace_id:
        return None

    # TODO: make this configurable?
    jobs_honeycomb_url = furl(
        "https://ui.honeycomb.io/bennett-institute-for-applied-data-science/environments/production/datasets/jobrunner"
    )
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
