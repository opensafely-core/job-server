"""
Functions for  specific slack messages jobserver sends.

These functions should always take a `channel` argument, so that we can test
them on a different channel.
"""

from django.conf import settings
from django.contrib.humanize.templatetags.humanize import naturalday
from furl import furl

from services import slack

from .utils import strip_whitespace


def notify_github_release(
    path, created_by, files, backend, channel="opensafely-releases"
):
    """
    path: path on level 4 server
    files: optional list of files released
    backend: backend released from
    """
    if files is not None:
        message = [
            f"{created_by} released {len(files)} outputs from {path} on {backend.name}:"
        ]
        for f in files:
            message.append(f"`{f}`")
    else:
        message = [f"{created_by} released outputs from {path} on {backend.name}"]

    slack.post(text="\n".join(message), channel=channel)


def notify_release_created(release, channel="opensafely-releases"):
    workspace_url = slack.link(
        release.workspace.get_absolute_url(), release.workspace.name
    )
    release_url = slack.link(release.get_absolute_url(), "release")
    user_url = slack.link(release.created_by.get_staff_url(), release.created_by.name)

    message = f"New {release_url} requested by {user_url}. {len(release.requested_files)} files for {workspace_url} from `{release.backend.name}`"

    slack.post(message, channel)


def notify_release_file_uploaded(rfile, channel="opensafely-releases"):
    release = rfile.release
    user = rfile.created_by

    workspace_url = slack.link(
        release.workspace.get_absolute_url(), release.workspace.name
    )
    user_url = slack.link(user.get_staff_url(), user.name)
    release_url = slack.link(release.get_absolute_url(), "release")
    file_url = slack.link(rfile.get_absolute_url(), rfile.name)

    size = round(rfile.size, 1)
    if size < 1:  # pragma: no cover
        size = "<1"

    message = f"{user_url} uploaded {file_url} ({rfile:Mb}) to a {release_url} for {workspace_url} from `{release.backend.name}`"
    slack.post(message, channel)


def notify_new_user(user, channel="job-server-registrations"):
    slack.post(
        text=f"New user ({user.username}) registered: {slack.link(user.get_staff_url())}",
        channel=channel,
    )


def notify_application(application, user, msg, channel="job-server-applications"):
    """
    Send a message to slack about an Application instance

    Derives URLs from the given Application and User instances, to build the
    Slack message using the given msg prefix.
    """
    slack.post(
        text=f"{msg} by {slack.link(user.get_staff_url(), user.username)}: {slack.link(application.get_staff_url())}",
        channel=channel,
    )


def notify_copilot_windows_closing(projects, channel="co-pilot-support"):
    def build_line(p):
        end_date = naturalday(p.copilot_support_ends_at)
        return f"\n * {slack.link(p.get_staff_url(), p.name)} ({end_date})"

    project_urls = [build_line(p) for p in projects]
    message = f"Projects with support window ending soon:{''.join(project_urls)}"

    slack.post(text=message, channel=channel)


def notify_copilots_of_repo_sign_off(repo, channel="co-pilot-support"):
    repo_link = slack.link(repo.get_staff_url(), repo.name)

    user_link = slack.link(
        repo.researcher_signed_off_by.get_staff_url(),
        repo.researcher_signed_off_by.name,
    )

    project = repo.workspaces.first().project
    project_link = slack.link(project.get_absolute_url(), project.slug)

    docs_link = slack.link(
        "https://bennettinstitute-team-manual.pages.dev/products/opensafely-jobs/#internal-repo-sign-off",
        "here",
    )

    message = [
        f"The {repo_link} repo was signed off by {user_link}.",
        f"It now needs to be signed off internally (see docs {docs_link}).",
        "",
        f"Project: {project_link}",
    ]

    copilot = project.copilot
    if copilot:
        copilot_link = slack.link(copilot.get_staff_url(), copilot.name)
    else:  # pragma: no cover
        copilot_link = "none"
    message.append(f"Copilot: {copilot_link}")

    slack.post(text="\n".join(message), channel=channel)


def notify_copilots_of_publish_request(
    publish_request, issue_url, channel="co-pilot-support"
):
    report_url = furl(settings.BASE_URL) / publish_request.report.get_absolute_url()

    message = f"""
    *Request to publish a report*
    By: {publish_request.created_by.email}
    GitHub Issue: {issue_url}

    {report_url}
    """

    message = strip_whitespace(message)

    slack.post(text=message, channel=channel)
