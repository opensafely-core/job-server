from unittest.mock import patch

import pytest
from requests.exceptions import HTTPError

from airlock.views import airlock_event_view
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
        raise HTTPError()

    def create_issue_comment(*args, **kwargs):
        raise HTTPError()

    def close_issue(*args, **kwargs):
        raise HTTPError()


@pytest.mark.parametrize(
    "event_type,author_is_user,updates,email_sent",
    [
        # author and user are different; emails are sent for rejected/released
        ("request_submitted", True, None, False),
        ("request_rejected", True, None, True),
        ("request_withdrawn", True, None, False),
        ("request_released", True, None, True),
        # author and user are the same; emails are still sent for rejected/released
        ("request_submitted", True, None, False),
        ("request_rejected", True, None, True),
        ("request_withdrawn", True, None, False),
        ("request_released", True, None, True),
        # updated; emails are sent if at least one update is not by the author
        (
            "request_updated",
            True,
            [{"update_type": "file_added", "group": "Group 1", "user": "test_user"}],
            True,
        ),
        (
            "request_updated",
            False,
            [
                {"update_type": "context_edited", "group": "Group 2", "user": "author"},
            ],
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
        ),
    ],
)
@patch("airlock.views._get_github_api", FakeGitHubAPI)
def test_api_post_release_request_post_by_non_author(
    api_rf, mailoutbox, event_type, author_is_user, updates, email_sent
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


@pytest.mark.parametrize(
    "event_type,updates,error",
    [
        ("request_submitted", None, "Error creating GitHub issue"),
        ("request_rejected", None, "Error closing GitHub issue"),
        (
            "request_updated",
            [{"update_type": "file_added", "group": "Group 1", "user": "user"}],
            "Error creating GitHub issue comment",
        ),
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
