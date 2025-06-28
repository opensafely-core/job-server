from unittest.mock import patch

import pytest

from airlock.config import ORG_OUTPUT_CHECKING_REPOS
from airlock.views import AirlockEvent, EventType, airlock_event_view
from tests.factories import (
    BackendFactory,
    BackendMembershipFactory,
    OrgFactory,
    ProjectFactory,
    ReleaseFactory,
    UserFactory,
    WorkspaceFactory,
)
from tests.fakes import FakeGitHubAPI, FakeGitHubAPIWithErrors


@pytest.mark.parametrize(
    "event_type,author_is_user,updates,email_sent,slack_notified",
    [
        # emails are sent for approved/rejected/released/returned
        # slack notifications are sent for resubmitted/partially_reviewed/reviewed
        ("request_submitted", True, None, False, False),
        ("request_rejected", False, None, True, False),
        ("request_withdrawn", True, None, False, False),
        (
            "request_approved",
            False,
            [{"update": "3 files will be uploaded"}],
            True,
            True,
        ),
        ("request_released", False, None, True, False),
        ("request_returned", False, None, True, True),
        ("request_resubmitted", True, None, False, True),
        ("request_partially_reviewed", False, None, False, True),
        ("request_reviewed", False, None, False, True),
    ],
)
@patch("airlock.views._get_github_api", FakeGitHubAPI)
def test_api_post_release_request_event(
    api_rf,
    mailoutbox,
    slack_messages,
    event_type,
    author_is_user,
    updates,
    email_sent,
    slack_notified,
):
    author = UserFactory(username="author")
    if author_is_user:
        user = author
    else:
        user = UserFactory(username="user")
    WorkspaceFactory(name="test-workspace")
    backend = BackendFactory(auth_token="test", name="test-backend")
    BackendMembershipFactory(backend=backend, user=user)

    if event_type in ["request_approved", "request_released"]:
        ReleaseFactory(id="01AAA1AAAAAAA1AAAAA11A1AAA")

    data = {
        "event_type": event_type,
        "updates": updates,
        "workspace": "test-workspace",
        "request": "01AAA1AAAAAAA1AAAAA11A1AAA",
        "request_author": author.username,
        "user": user.username,
    }
    request = api_rf.post(
        "/",
        data=data,
        format="json",
        headers={
            "authorization": "test",
            "os-user": user.username,
        },
    )
    response = airlock_event_view(request)
    assert response.status_code == 201
    assert response.data == {"status": "ok"}

    if email_sent:
        assert len(mailoutbox) == 1
    else:
        assert len(mailoutbox) == 0

    if slack_notified:
        assert len(slack_messages) == 1
    else:
        assert len(slack_messages) == 0


@patch("airlock.views._get_github_api", FakeGitHubAPI)
@patch("airlock.views.create_output_checking_issue")
def test_api_post_release_request_custom_org_and_repo(mock_create_issue, api_rf):
    mock_create_issue.return_value = "http://example.com"
    author = UserFactory(username="author")
    workspace = WorkspaceFactory(
        name="test-workspace",
        project=ProjectFactory(org=OrgFactory(slug="test-org")),
    )
    backend = BackendFactory(auth_token="test", name="test-backend")
    BackendMembershipFactory(backend=backend, user=author)

    data = {
        "event_type": "request_submitted",
        "updates": None,
        "workspace": "test-workspace",
        "request": "01AAA1AAAAAAA1AAAAA11A1AAA",
        "request_author": author.username,
        "user": author.username,
        "org": "foo",
        "repo": "bar",
    }
    request = api_rf.post(
        "/",
        data=data,
        format="json",
        headers={
            "authorization": "test",
            "os-user": author.username,
        },
    )
    response = airlock_event_view(request)
    assert response.status_code == 201
    assert response.data == {"status": "ok"}

    assert list(mock_create_issue.call_args.args[:-1]) == [
        workspace,
        "01AAA1AAAAAAA1AAAAA11A1AAA",
        author,
        "foo",
        "bar",
    ]


@patch("airlock.views._get_github_api", FakeGitHubAPI)
@patch("airlock.views.create_output_checking_issue")
def test_api_post_release_request_non_default_org_and_repo(
    mock_create_issue, api_rf, monkeypatch
):
    repos = ORG_OUTPUT_CHECKING_REPOS.copy()
    repos["non-default-university"] = {
        "org": "ebmdatalab",
        "repo": "opensafely-output-review-non-default",
    }
    monkeypatch.setattr("airlock.views.ORG_OUTPUT_CHECKING_REPOS", repos)

    mock_create_issue.return_value = "http://example.com"
    author = UserFactory(username="author")
    workspace = WorkspaceFactory(
        name="test-workspace",
        project=ProjectFactory(org=OrgFactory(slug="non-default-university")),
    )
    backend = BackendFactory(auth_token="test", name="test-backend")
    BackendMembershipFactory(backend=backend, user=author)

    data = {
        "event_type": "request_submitted",
        "updates": None,
        "workspace": "test-workspace",
        "request": "01AAA1AAAAAAA1AAAAA11A1AAA",
        "request_author": author.username,
        "user": author.username,
    }
    request = api_rf.post(
        "/",
        data=data,
        format="json",
        headers={
            "authorization": "test",
            "os-user": author.username,
        },
    )
    response = airlock_event_view(request)
    assert response.status_code == 201
    assert response.data == {"status": "ok"}

    assert list(mock_create_issue.call_args.args[:-1]) == [
        workspace,
        "01AAA1AAAAAAA1AAAAA11A1AAA",
        author,
        "ebmdatalab",
        "opensafely-output-review-non-default",
    ]


@patch("airlock.views._get_github_api", FakeGitHubAPI)
@patch("airlock.views.create_output_checking_issue")
def test_api_post_release_request_default_org_and_repo(mock_create_issue, api_rf):
    mock_create_issue.return_value = "http://example.com"
    author = UserFactory(username="author")
    workspace = WorkspaceFactory(
        name="test-workspace",
        project=ProjectFactory(org=OrgFactory(slug="test-org")),
    )
    backend = BackendFactory(auth_token="test", name="test-backend")
    BackendMembershipFactory(backend=backend, user=author)

    data = {
        "event_type": "request_submitted",
        "updates": None,
        "workspace": "test-workspace",
        "request": "01AAA1AAAAAAA1AAAAA11A1AAA",
        "request_author": author.username,
        "user": author.username,
    }
    request = api_rf.post(
        "/",
        data=data,
        format="json",
        headers={
            "authorization": "test",
            "os-user": author.username,
        },
    )
    response = airlock_event_view(request)
    assert response.status_code == 201
    assert response.data == {"status": "ok"}

    assert list(mock_create_issue.call_args.args[:-1]) == [
        workspace,
        "01AAA1AAAAAAA1AAAAA11A1AAA",
        author,
        "ebmdatalab",
        "test-repo",
    ]


@pytest.mark.parametrize(
    "event_type,updates,error,slack_notified",
    [
        (
            "request_submitted",
            None,
            "Error creating GitHub issue: An error occurred",
            False,
        ),
        (
            "request_rejected",
            None,
            "Error closing GitHub issue: An error occurred",
            False,
        ),
        (
            "request_returned",
            None,
            "Error creating GitHub issue comment: An error occurred",
            True,
        ),
        (
            "request_resubmitted",
            None,
            "Error creating GitHub issue comment: An error occurred",
            True,
        ),
        ("bad_event_type", None, "Unknown event type 'BAD_EVENT_TYPE'", False),
    ],
)
@patch("airlock.views._get_github_api", FakeGitHubAPIWithErrors)
@patch("airlock.issues.settings.DEFAULT_MAX_GITHUB_RETRIES", 1)
def test_api_airlock_event_error(
    api_rf, slack_messages, event_type, updates, error, slack_notified
):
    author = UserFactory()
    user = UserFactory()
    WorkspaceFactory(name="test-workspace")
    backend = BackendFactory(auth_token="test", name="test-backend")
    BackendMembershipFactory(backend=backend, user=user)

    data = {
        "event_type": event_type,
        "updates": updates,
        "workspace": "test-workspace",
        "request": "01AAA1AAAAAAA1AAAAA11A1AAA",
        "request_author": author.username,
        "user": user.username,
    }
    request = api_rf.post(
        "/",
        data=data,
        format="json",
        headers={
            "authorization": "test",
            "os-user": user.username,
        },
    )
    response = airlock_event_view(request)
    assert response.status_code == 201
    assert response.data == {
        "status": "error",
        "message": error,
    }

    # For notifications that send slack messages, GitHub errors don't prevent
    # the slack notifications from being sent. The github error is reported
    # in the slack message.
    if slack_notified:
        assert len(slack_messages) == 1
        assert "A GitHub error occurred" in slack_messages[0][0]
    else:
        assert len(slack_messages) == 0


@patch("airlock.views._get_github_api", FakeGitHubAPIWithErrors)
@patch("airlock.emails.send_html_email")
@patch("airlock.issues.settings.DEFAULT_MAX_GITHUB_RETRIES", 1)
def test_api_airlock_event_multiple_errors(mock_send, api_rf, slack_messages):
    mock_send.side_effect = Exception("Error sending email")
    author = UserFactory()
    user = UserFactory()
    WorkspaceFactory(name="test-workspace")
    backend = BackendFactory(auth_token="test", name="test-backend")
    BackendMembershipFactory(backend=backend, user=user)
    ReleaseFactory(id="01AAA1AAAAAAA1AAAAA11A1AAA")

    # A request approved event sends 3 notifications:
    # - sends an email that includes the release URL,
    # - updates the github issue
    # - posts to slack
    # This notification attempt will error on sending the email, and then
    # it'll also error creating the GitHub issue update. All events will
    # be attempted, and the two errors will be reported in the response
    data = {
        "event_type": "request_approved",
        "updates": None,
        "workspace": "test-workspace",
        "request": "01AAA1AAAAAAA1AAAAA11A1AAA",
        "request_author": author.username,
        "user": user.username,
    }

    request = api_rf.post(
        "/",
        data=data,
        format="json",
        headers={
            "authorization": "test",
            "os-user": user.username,
        },
    )
    response = airlock_event_view(request)
    assert response.status_code == 201
    assert response.data == {
        "status": "error",
        "message": (
            "Error sending email; "
            "Error creating GitHub issue comment: An error occurred"
        ),
    }
    # still sends the slack message
    assert len(slack_messages) == 1


@pytest.mark.parametrize(
    "event_type,user,updates,descriptions",
    [
        (
            EventType.REQUEST_SUBMITTED,
            "author",
            [],
            ["request submitted by user author"],
        ),
        (
            EventType.REQUEST_WITHDRAWN,
            "author",
            [],
            ["request withdrawn by user author"],
        ),
        (EventType.REQUEST_APPROVED, "user1", [], ["request approved by user user1"]),
        (EventType.REQUEST_RELEASED, "user1", [], ["request released by user user1"]),
        (EventType.REQUEST_REJECTED, "user1", [], ["request rejected by user user1"]),
        (EventType.REQUEST_RETURNED, "user1", [], ["request returned by user user1"]),
        (
            EventType.REQUEST_RESUBMITTED,
            "author",
            [],
            ["request resubmitted by user author"],
        ),
        (
            EventType.REQUEST_PARTIALLY_REVIEWED,
            "user1",
            [],
            ["request reviewed by user user1"],
        ),
        (EventType.REQUEST_REVIEWED, "user2", [], ["request reviewed by user user2"]),
        (
            EventType.REQUEST_RETURNED,
            "user1",
            [
                {"update_type": "comment added", "user": "user_a", "group": "group"},
                {"update": "a thing was updated"},
                {"update": "another thing updated", "user": "user_b"},
                {"update": "thing X updated", "user": "user_b", "group": "group"},
            ],
            [
                "request returned by user user1",
                "comment added (filegroup group) by user user_a",
                "a thing was updated",
                "another thing updated by user user_b",
                "thing X updated (filegroup group) by user user_b",
            ],
        ),
    ],
)
def test_airlock_event_describe_updates(event_type, user, updates, descriptions):
    users = {
        "author": UserFactory(username="author"),
        "user1": UserFactory(username="user1"),
        "user2": UserFactory(username="user2"),
    }

    workspace = WorkspaceFactory(name="test-workspace")
    backend = BackendFactory(auth_token="test", name="test-backend")
    BackendMembershipFactory(backend=backend, user=users["user1"])

    airlock_event = AirlockEvent(
        event_type=event_type,
        workspace=workspace,
        updates=updates,
        release_request_id="request-id",
        request_author=users["author"],
        user=users[user],
        org="org",
        repo="repo",
    )
    assert airlock_event.describe_updates() == descriptions

    assert airlock_event.describe_updates_as_str() == "\n".join(
        [f"- {description}" for description in descriptions]
    )
