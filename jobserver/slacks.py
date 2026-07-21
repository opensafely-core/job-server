"""
Functions for  specific slack messages jobserver sends.

These functions should always take a `channel` argument, so that we can test
them on a different channel.
"""

from django.conf import settings
from django.contrib.humanize.templatetags.humanize import naturalday

from services import slack


def notify_new_user(user, channel=settings.REGISTRATIONS_SLACK_CHANNEL):
    slack.post(
        text=f"New user ({user.username}) registered: {slack.link(user.get_staff_url())}",
        channel=channel,
    )


def notify_application(
    application, user, msg, channel=settings.APPLICATIONS_SLACK_CHANNEL
):
    """
    Send a message to slack about an Application instance

    Derives URLs from the given Application and User instances, to build the
    Slack message using the given msg prefix.
    """
    slack.post(
        text=f"{msg} by {slack.link(user.get_staff_url(), user.username)}: {slack.link(application.get_staff_url())}",
        channel=channel,
    )


def notify_copilots_project_added(
    project, channel=settings.COPILOT_SUPPORT_SLACK_CHANNEL
):
    project_url = slack.link(project.get_staff_url(), project.title)
    user_url = slack.link(
        project.created_by.get_staff_url(), project.created_by.fullname
    )
    copilot_url = (
        "Copilot: "
        f"{slack.link(project.copilot.get_staff_url(), project.copilot.fullname)}."
        if project.copilot
        # Don't list copilot at all if not set, as it may be confusing to state
        # Copilot: none as they may exist but be missing in the database.
        else ""
    )

    message = (
        f"The {project_url} project was created by {user_url}. Please "
        "update the tracking board and contact users. "
        f"{copilot_url}"
    )

    slack.post(message, channel)


def notify_copilot_windows_closing(
    projects, channel=settings.COPILOT_SUPPORT_SLACK_CHANNEL
):
    def build_line(p):
        end_date = naturalday(p.copilot_support_ends_at)
        return f"\n * {slack.link(p.get_staff_url(), p.name)} ({end_date})"

    project_urls = [build_line(p) for p in projects]
    message = f"Projects with support window ending soon:{''.join(project_urls)}"

    slack.post(text=message, channel=channel)


def notify_copilots_of_repo_sign_off(
    repo, channel=settings.COPILOT_SUPPORT_SLACK_CHANNEL
):
    repo_link = slack.link(repo.get_staff_url(), repo.name)

    user_link = slack.link(
        repo.researcher_signed_off_by.get_staff_url(),
        repo.researcher_signed_off_by.fullname,
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
        copilot_link = slack.link(copilot.get_staff_url(), copilot.fullname)
    else:
        copilot_link = "none"
    message.append(f"Copilot: {copilot_link}")

    slack.post(text="\n".join(message), channel=channel)


def alert_raw_dump(channel=settings.ALERTS_SLACK_CHANNEL):
    policy_link = slack.link(
        "https://bennett.wiki/tech-group/policies/personal-data-copying-policy/",
        "personal data copying policy",
    )
    log_link = slack.link(
        "https://docs.google.com/spreadsheets/d/1C1z3WV-WSL-H1keZZCVPm6hR_5ajjgRT5zGO5cLv2Aw",
        "personal data copying decision log",
    )
    message = (
        "Someone ran `dump_raw_data` to generate a raw Job Server database dump. "
        f"The {policy_link} must be followed. The copying of raw personal data must "
        f"be recorded in {log_link}. The raw dump must be removed from the server "
        "and developer machines as soon as it is no longer required."
    )
    slack.post(text=message, channel=channel)
