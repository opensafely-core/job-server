"""
Functions for specific slack messages jobserver sends.

These functions should always take a `channel` argument, so that we can test
them on a different channel.
"""
from jobserver.utils import strip_whitespace
from services import slack


def notify_analysis_request_submitted(analysis_request, channel="interactive-requests"):
    analysis_url = slack.link(analysis_request.get_absolute_url(), "View on job-server")
    commit_url = slack.link(
        analysis_request.job_request.get_repo_url(), analysis_request.job_request.sha
    )
    job_request_url = slack.link(
        analysis_request.job_request.get_absolute_url(), analysis_request.job_request.pk
    )

    message = f"""
    *Analysis Requested*
    By: {analysis_request.created_by.email}
    Title: {analysis_request.title}
    Commit: {commit_url}
    Job Request: {job_request_url}

    {analysis_url}
    """

    message = strip_whitespace(message)

    slack.post(message, channel)


def notify_tech_support_of_failed_analysis(job_request, channel="tech-support-channel"):
    """
    Notify tech support when an Interactive analysis fails

    Interactive users aren't expected to track the status of their job requests
    in job-server because we show them a higher level interface, so it's
    reasonable to think they would not be monitoring for failed jobs.  A failed
    job for an Interactive request also likely represents a bug since the code
    is written by OpenSAFELY, and tech support will triage this for us.
    """
    job_request_url = slack.link(job_request.get_absolute_url(), "view it here")

    message = f"An analysis request has failed, {job_request_url}."

    slack.post(message, channel)


def notify_report_uploaded(analysis_request, channel="interactive-requests"):
    analysis_url = slack.link(analysis_request.get_absolute_url(), "View on job-server")

    message = f"""
    *Report uploaded*
    Title: {analysis_request.report_title}

    {analysis_url}
    """

    message = strip_whitespace(message)

    slack.post(message, channel)
