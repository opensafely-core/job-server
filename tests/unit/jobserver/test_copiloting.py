from datetime import timedelta

from django.contrib.humanize.templatetags.humanize import naturalday
from django.utils import timezone

from jobserver.copiloting import notify_impending_copilot_windows_closing

from ...factories import ProjectFactory


def test_notify_impending_copilot_windows_closing_multiple_projects(mocker):
    project1 = ProjectFactory(
        copilot_support_ends_at=timezone.now() + timedelta(days=1)
    )
    project2 = ProjectFactory(
        copilot_support_ends_at=timezone.now() + timedelta(days=2)
    )
    project3 = ProjectFactory(
        copilot_support_ends_at=timezone.now() + timedelta(days=3)
    )

    mocked_slack = mocker.patch("jobserver.copiloting.slack_client", autospec=True)

    assert notify_impending_copilot_windows_closing() is None

    def line(project):
        end_date = naturalday(project.copilot_support_ends_at)
        url = f"http://localhost:8000{project.get_staff_url()}"
        return f"\n * <{url}|{project.name}> ({end_date})"

    message = f"Projects with support window ending soon:{line(project1)}{line(project2)}{line(project3)}"

    assert mocked_slack.chat_postMessage.call_count == 1
    mocked_slack.chat_postMessage.assert_called_with(
        channel="co-pilot-support",
        text=message,
    )


def test_notify_impending_copilot_windows_closing_no_projects(mocker, log_output):
    assert len(log_output.entries) == 0, log_output.entries

    mocked_slack = mocker.patch("jobserver.copiloting.slack_client", autospec=True)

    assert notify_impending_copilot_windows_closing() is None

    mocked_slack.chat_postMessage.assert_not_called()

    # check we logged the lack of projects
    assert len(log_output.entries) == 1, log_output.entries
    assert log_output.entries[0] == {
        "event": "No projects with copilot support windows closing within 5 days",
        "log_level": "info",
    }


def test_notify_impending_copilot_windows_closing_one_project(mocker):
    project = ProjectFactory(copilot_support_ends_at=timezone.now() + timedelta(days=3))

    mocked_slack = mocker.patch("jobserver.copiloting.slack_client", autospec=True)

    assert notify_impending_copilot_windows_closing() is None

    end_date = naturalday(project.copilot_support_ends_at)
    url = f"http://localhost:8000{project.get_staff_url()}"
    line = f"\n * <{url}|{project.name}> ({end_date})"
    message = f"Projects with support window ending soon:{line}"

    assert mocked_slack.chat_postMessage.call_count == 1
    mocked_slack.chat_postMessage.assert_called_with(
        channel="co-pilot-support",
        text=message,
    )


def test_notify_impending_copilot_windows_closing_with_DEBUG(mocker, settings):
    settings.DEBUG = True

    mocked_slack = mocker.patch("jobserver.copiloting.slack_client", autospec=True)

    assert notify_impending_copilot_windows_closing() is None

    mocked_slack.chat_postMessage.assert_not_called()
