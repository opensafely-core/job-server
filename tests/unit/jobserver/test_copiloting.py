from datetime import timedelta

from django.contrib.humanize.templatetags.humanize import naturalday
from django.utils import timezone

from jobserver.copiloting import notify_impending_copilot_windows_closing

from ...factories import ProjectFactory


def test_notify_impending_copilot_windows_closing_multiple_projects(slack_messages):
    project1 = ProjectFactory(
        copilot_support_ends_at=timezone.now() + timedelta(days=1)
    )
    project2 = ProjectFactory(
        copilot_support_ends_at=timezone.now() + timedelta(days=2)
    )
    project3 = ProjectFactory(
        copilot_support_ends_at=timezone.now() + timedelta(days=3)
    )

    assert notify_impending_copilot_windows_closing() is None

    def line(project):
        end_date = naturalday(project.copilot_support_ends_at)
        url = f"http://localhost:8000{project.get_staff_url()}"
        return f"\n * <{url}|{project.name}> ({end_date})"

    expected = f"Projects with support window ending soon:{line(project1)}{line(project2)}{line(project3)}"

    assert len(slack_messages) == 1
    text, channel = slack_messages[0]
    assert channel == "co-pilot-support"
    assert text == expected


def test_notify_impending_copilot_windows_closing_no_projects(
    slack_messages, log_output
):
    assert len(log_output.entries) == 0, log_output.entries

    assert notify_impending_copilot_windows_closing() is None

    assert len(slack_messages) == 0

    # check we logged the lack of projects
    assert len(log_output.entries) == 1, log_output.entries
    assert log_output.entries[0] == {
        "event": "No projects with copilot support windows closing within 5 days",
        "log_level": "info",
    }


def test_notify_impending_copilot_windows_closing_one_project(slack_messages):
    project = ProjectFactory(copilot_support_ends_at=timezone.now() + timedelta(days=3))

    assert notify_impending_copilot_windows_closing() is None

    end_date = naturalday(project.copilot_support_ends_at)
    url = f"http://localhost:8000{project.get_staff_url()}"
    line = f"\n * <{url}|{project.name}> ({end_date})"
    expected = f"Projects with support window ending soon:{line}"

    assert len(slack_messages) == 1
    text, channel = slack_messages[0]
    assert channel == "co-pilot-support"
    assert text == expected
