import pytest
from django.utils import timezone

from jobserver.slacks import (
    notify_copilots_of_repo_sign_off,
    notify_copilots_project_added,
)
from tests.factories import ProjectFactory, RepoFactory, UserFactory, WorkspaceFactory


@pytest.mark.parametrize(
    "copilot_assigned", [True, False], ids=["with_copilot", "without_copilot"]
)
def test_notify_copilots_project_added(copilot_assigned, slack_messages):
    """Test output of notify_copilots_project_added. Parameterised: copilot vs no copilot."""
    # Given a project created by a user with/without a copilot.
    creator = UserFactory()
    # Create project with or without a copilot according to the parameter.
    if copilot_assigned:
        copilot = UserFactory()
        project = ProjectFactory(copilot=copilot, created_by=creator)
        expected_copilot_name = copilot.fullname
    else:
        project = ProjectFactory(created_by=creator)
        expected_copilot_name = None

    # When the function under test is called on the repo.
    notify_copilots_project_added(project)

    # Then one Slack message gets sent to the right channel.
    assert len(slack_messages) == 1
    message, channel = slack_messages[0]
    assert channel == "co-pilot-support"

    # ...and message contains expected values.
    # Testing for the full message content would be too brittle to changes.
    assert project.title in message
    assert creator.fullname in message
    assert "was created" in message
    # Case-specific assertion, depending whether we have a copilot.
    if expected_copilot_name is not None:
        assert expected_copilot_name in message
    else:
        assert "copilot" not in message.lower()


@pytest.mark.parametrize(
    "copilot_assigned", [True, False], ids=["with_copilot", "without_copilot"]
)
def test_notify_copilots_of_repo_sign_off(copilot_assigned, slack_messages):
    """Test output of notify_copilots_of_repo_sign_off. Parameterised: copilot vs no copilot."""
    # Given a signed off repo with/without a copilot, linked to a project via workspace.
    researcher = UserFactory()
    repo = RepoFactory(
        researcher_signed_off_by=researcher,
        researcher_signed_off_at=timezone.now(),
    )
    # Create project with or without a copilot according to the parameter.
    if copilot_assigned:
        copilot = UserFactory()
        project = ProjectFactory(copilot=copilot)
        expected_copilot_fragment = copilot.fullname
    else:
        project = ProjectFactory()
        expected_copilot_fragment = "Copilot: none"
    WorkspaceFactory(repo=repo, project=project)

    assert len(slack_messages) == 0

    # When the function under test is called on the repo.
    notify_copilots_of_repo_sign_off(repo)

    # Then one Slack message gets sent to the right channel.
    assert len(slack_messages) == 1
    message, channel = slack_messages[0]
    assert channel == "co-pilot-support"

    # ...and message contains expected values, including right copilot fragment.
    # Testing for the full message content would be too brittle to changes.
    assert repo.name in message
    assert project.slug in message
    assert "<https://bennettinstitute-team-manual.pages.dev" in message
    assert researcher.fullname in message
    # Case-specific assertion, depending whether we have a copilot.
    assert expected_copilot_fragment in message
