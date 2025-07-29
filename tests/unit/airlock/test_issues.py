from unittest.mock import patch

from django.conf import settings

from airlock.issues import (
    IssueStatusLabel,
    close_output_checking_issue,
    create_output_checking_issue,
    update_output_checking_issue,
)
from jobserver.github import GitHubError
from tests.factories import (
    OrgFactory,
    OrgMembershipFactory,
    UserFactory,
    WorkspaceFactory,
)
from tests.fakes import FakeGitHubAPI


def test_create_output_checking_request_external(github_api):
    user = UserFactory()
    workspace = WorkspaceFactory(name="test-workspace")

    assert (
        create_output_checking_issue(
            workspace,
            "01AAA1AAAAAAA1AAAAA11A1AAA",
            user,
            "ebmdatalab",
            "opensafely-output-review",
            github_api,
        )
        == "http://example.com"
    )

    issue = next(i for i in github_api.issues if i)  # pragma: no branch

    assert set(issue.labels) == {"external", IssueStatusLabel.PENDING_REVIEW.value}
    assert issue.org == "ebmdatalab"
    assert issue.repo == "opensafely-output-review"
    assert issue.title == "test-workspace 01AAA1AAAAAAA1AAAAA11A1AAA"

    lines = issue.body.split("\n")
    assert user.fullname in lines[0]
    assert lines[1] == "Release request ID: 01AAA1AAAAAAA1AAAAA11A1AAA"
    assert workspace.repo.name in lines[2]
    assert workspace.name in lines[3]


def test_create_output_checking_request_internal(github_api):
    org = OrgFactory(pk=settings.BENNETT_ORG_PK)
    user = UserFactory()
    OrgMembershipFactory(org=org, user=user)
    workspace = WorkspaceFactory(name="test-workspace")

    assert (
        create_output_checking_issue(
            workspace,
            "01AAA1AAAAAAA1AAAAA11A1AAA",
            user,
            "ebmdatalab",
            "opensafely-output-review",
            github_api,
        )
        == "http://example.com"
    )

    issue = next(i for i in github_api.issues if i)  # pragma: no branch

    assert set(issue.labels) == {"internal", IssueStatusLabel.PENDING_REVIEW.value}
    assert issue.org == "ebmdatalab"
    assert issue.repo == "opensafely-output-review"
    assert issue.title == "test-workspace 01AAA1AAAAAAA1AAAAA11A1AAA"

    lines = issue.body.split("\n")
    assert user.fullname in lines[0]
    assert lines[1] == "Release request ID: 01AAA1AAAAAAA1AAAAA11A1AAA"
    assert workspace.repo.name in lines[2]
    assert workspace.name in lines[3]


def test_create_output_checking_request_no_label_matches(github_api):
    class GithubApiWithMismatchedLabels(github_api.__class__):
        def get_labels(self, org, repo):
            return ["a label"]

    user = UserFactory()
    workspace = WorkspaceFactory(name="test-workspace")
    github_api_with_mismatched_labels = GithubApiWithMismatchedLabels()
    assert (
        create_output_checking_issue(
            workspace,
            "01AAA1AAAAAAA1AAAAA11A1AAA",
            user,
            "ebmdatalab",
            "repo-without-internal-external-labels",
            github_api_with_mismatched_labels,
        )
        == "http://example.com"
    )

    issue = next(i for i in github_api.issues if i)  # pragma: no branch

    # the default label is "external", but it doesn't exist for this repo
    # so we just ignore it
    assert issue.labels == [IssueStatusLabel.PENDING_REVIEW.value]
    assert issue.org == "ebmdatalab"
    assert issue.repo == "repo-without-internal-external-labels"
    assert issue.title == "test-workspace 01AAA1AAAAAAA1AAAAA11A1AAA"
    # new labels (github_abi fixture returns just [] for the repo's labels)
    assert len(github_api.labels) == 3
    new_labels = {label.label_name for label in github_api.labels}
    assert new_labels == {
        IssueStatusLabel.PENDING_REVIEW.value,
        IssueStatusLabel.UNDER_REVIEW.value,
        IssueStatusLabel.WITH_REQUESTER.value,
    }


def test_close_output_checking_request(github_api):
    org = OrgFactory(pk=settings.BENNETT_ORG_PK)
    user = UserFactory()
    OrgMembershipFactory(org=org, user=user)
    assert (
        close_output_checking_issue(
            "01AAA1AAAAAAA1AAAAA11A1AAA",
            user,
            "Closed for reasons",
            "ebmdatalab",
            "opensafely-output-review",
            github_api,
        )
        == "http://example.com/closed"
    )

    issue = next(i for i in github_api.closed_issues if i)  # pragma: no branch

    assert issue.org == "ebmdatalab"
    assert issue.repo == "opensafely-output-review"
    assert issue.title_text == "01AAA1AAAAAAA1AAAAA11A1AAA"
    assert issue.comment == f"Issue closed: Closed for reasons by {user.username}"
    # status labels have been removed, but other remain
    # (github api fixture always returns ["internal", "Under review"] for issue labels)
    assert issue.labels == ["internal"]

    comment = next(c for c in github_api.comments if c)  # pragma: no branch
    assert comment.org == "ebmdatalab"
    assert comment.repo == "opensafely-output-review"
    assert comment.title_text == "01AAA1AAAAAAA1AAAAA11A1AAA"
    assert comment.body == f"Issue closed: Closed for reasons by {user.username}"


def test_update_output_checking_request(github_api, slack_messages):
    org = OrgFactory(pk=settings.BENNETT_ORG_PK)
    user = UserFactory()
    OrgMembershipFactory(org=org, user=user)
    assert (
        update_output_checking_issue(
            "01AAA1AAAAAAA1AAAAA11A1AAA",
            "workspace",
            "- file added (filegroup 'Group 1') by user test",
            "ebmdatalab",
            "opensafely-output-review",
            github_api,
            notify_slack=False,
            request_author=user,
            label=IssueStatusLabel.WITH_REQUESTER,
        )
        == "http://example.com/issues/comment"
    )

    comment = next(c for c in github_api.comments if c)  # pragma: no branch
    assert comment.org == "ebmdatalab"
    assert comment.repo == "opensafely-output-review"
    assert comment.title_text == "01AAA1AAAAAAA1AAAAA11A1AAA"
    assert (
        comment.body
        == "Release request updated:\n- file added (filegroup 'Group 1') by user test"
    )
    assert set(comment.labels) == {"internal", IssueStatusLabel.WITH_REQUESTER.value}
    assert slack_messages == []


def test_update_output_checking_request_no_label(github_api, slack_messages):
    org = OrgFactory(pk=settings.BENNETT_ORG_PK)
    user = UserFactory()
    OrgMembershipFactory(org=org, user=user)
    assert (
        update_output_checking_issue(
            "01AAA1AAAAAAA1AAAAA11A1AAA",
            "workspace",
            ["request approved by user test"],
            "ebmdatalab",
            "opensafely-output-review",
            github_api,
            notify_slack=False,
            label=None,
        )
        == "http://example.com/issues/comment"
    )

    comment = next(c for c in github_api.comments if c)  # pragma: no branch
    assert comment.org == "ebmdatalab"
    assert comment.repo == "opensafely-output-review"
    assert comment.title_text == "01AAA1AAAAAAA1AAAAA11A1AAA"
    assert set(comment.labels) == {"internal"}


def test_update_output_checking_request_with_slack_notification(
    github_api, slack_messages
):
    org = OrgFactory(pk=settings.BENNETT_ORG_PK)
    user = UserFactory()
    OrgMembershipFactory(org=org, user=user)
    assert (
        update_output_checking_issue(
            "01",
            "workspace",
            "- request resubmitted by user test",
            "ebmdatalab",
            "opensafely-output-review",
            github_api,
            notify_slack=True,
            request_author=user,
            label=IssueStatusLabel.PENDING_REVIEW,
        )
        == "http://example.com/issues/comment"
    )
    assert len(slack_messages) == 1
    assert slack_messages == [
        (
            "<http://example.com/issues/comment|workspace 01 has been updated>\n- request resubmitted by user test",
            "test-channel",
        )
    ]


def test_create_output_checking_issue_retry_error_and_success():
    user = UserFactory()
    workspace = WorkspaceFactory(name="test-workspace")

    api = FakeGitHubAPI()

    with patch.object(api, "create_issue") as mock_create_issue:
        mock_create_issue.side_effect = [
            GitHubError,
            GitHubError,
            {"html_url": "http://example.com"},
        ]
        mock_issue = create_output_checking_issue(
            workspace,
            "01AAA1AAAAAAA1AAAAA11A1AAA",
            user,
            "ebmdatalab",
            "opensafely-output-review",
            api,
        )
    mock_create_issue.call_count == 3
    assert mock_issue == "http://example.com"
