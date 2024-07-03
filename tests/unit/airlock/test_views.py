from unittest.mock import patch

import pytest
from requests.exceptions import HTTPError

from airlock.views import AirlockEvent, EventType, airlock_event_view
from tests.factories import (
    BackendFactory,
    BackendMembershipFactory,
    ReleaseFactory,
    UserFactory,
    WorkspaceFactory,
)
from tests.fakes import FakeGitHubAPI


class FakeGithubApiWithError:
    def create_issue(*args, **kwargs):
        raise HTTPError("An error occurred")

    def create_issue_comment(*args, **kwargs):
        raise HTTPError("An error occurred")

    def close_issue(*args, **kwargs):
        raise HTTPError("An error occurred")


@pytest.mark.parametrize(
    "event_type,author_is_user,updates,email_sent,slack_notified",
    [
        # No action for request_approved
        ("request_approved", True, None, False, False),
        # author and user are different; emails are sent for rejected/released/returned
        # slack notifications are sent for resubmitted/partially_reviewed/reviewed
        ("request_submitted", False, None, False, False),
        ("request_rejected", False, None, True, False),
        ("request_withdrawn", False, None, False, False),
        ("request_released", False, None, True, False),
        ("request_returned", False, None, True, False),
        ("request_resubmitted", False, None, False, True),
        ("request_partially_reviewed", False, None, False, True),
        ("request_reviewed", False, None, False, True),
        # author and user are the same; emails are still sent for rejected/released/returned
        # slack notifications are still sent for resubmitted/partially_reviewed/reviewed
        ("request_submitted", True, None, False, False),
        ("request_rejected", True, None, True, False),
        ("request_withdrawn", True, None, False, False),
        ("request_released", True, None, True, False),
        ("request_returned", True, None, True, False),
        ("request_resubmitted", True, None, False, True),
        ("request_partially_reviewed", True, None, False, True),
        ("request_reviewed", True, None, False, True),
        # updated; emails are sent if at least one update is not by the author
        (
            "request_updated",
            True,
            [{"update_type": "file_added", "group": "Group 1", "user": "test_user"}],
            True,
            False,
        ),
        (
            "request_updated",
            False,
            [
                {"update_type": "context_edited", "group": "Group 2", "user": "author"},
            ],
            False,
            False,
        ),
        (
            "request_updated",
            False,
            [
                {
                    "update_type": "comment_added",
                    "group": "Group 1",
                    "user": "test_user",
                },
                {"update_type": "comment_added", "group": "Group 1", "user": "author"},
            ],
            True,
            False,
        ),
    ],
)
@patch("airlock.views._get_github_api", FakeGitHubAPI)
def test_api_post_release_request_post_by_non_author(
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

    if event_type == "request_released":
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
    workspace = WorkspaceFactory(name="test-workspace")
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
def test_api_post_release_request_default_org_and_repo(mock_create_issue, api_rf):
    mock_create_issue.return_value = "http://example.com"
    author = UserFactory(username="author")
    workspace = WorkspaceFactory(name="test-workspace")
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
    "event_type,updates,error",
    [
        ("request_submitted", None, "Error creating GitHub issue: An error occurred"),
        ("request_rejected", None, "Error closing GitHub issue: An error occurred"),
        (
            "request_updated",
            [{"update_type": "file_added", "group": "Group 1", "user": "user"}],
            "Error creating GitHub issue comment: An error occurred",
        ),
        (
            "request_returned",
            None,
            "Error creating GitHub issue comment: An error occurred",
        ),
        (
            "request_resubmitted",
            None,
            "Error creating GitHub issue comment: An error occurred",
        ),
        ("bad_event_type", None, "Unknown event type 'BAD_EVENT_TYPE'"),
    ],
)
@patch("airlock.views._get_github_api", FakeGithubApiWithError)
def test_api_airlock_event_error(api_rf, event_type, updates, error):

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


@pytest.mark.parametrize(
    "event_type,user,updates,descriptions",
    [
        (EventType.REQUEST_SUBMITTED, "author", [], []),
        (EventType.REQUEST_WITHDRAWN, "author", [], []),
        (EventType.REQUEST_APPROVED, "user1", [], []),
        (EventType.REQUEST_RELEASED, "user1", [], []),
        (EventType.REQUEST_REJECTED, "user1", [], []),
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
            EventType.REQUEST_UPDATED,
            "author",
            [
                {"update_type": "file_added", "group": "Group 1", "user": "author"},
                {"update_type": "context_edited", "group": "Group 2", "user": "author"},
            ],
            [
                "file_added (filegroup Group 1) by user author",
                "context_edited (filegroup Group 2) by user author",
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
