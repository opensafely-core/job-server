from django.conf import settings

from airlock.issues import (
    close_output_checking_issue,
    create_output_checking_issue,
    update_output_checking_issue,
)
from tests.factories import (
    OrgFactory,
    OrgMembershipFactory,
    UserFactory,
    WorkspaceFactory,
)


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

    issue = next((i for i in github_api.issues if i), None)  # pragma: no branch

    assert issue.labels == ["external"]
    assert issue.org == "ebmdatalab"
    assert issue.repo == "opensafely-output-review"
    assert issue.title == "test-workspace 01AAA1AAAAAAA1AAAAA11A1AAA"

    lines = issue.body.split("\n")
    assert user.name in lines[0]
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

    issue = next((i for i in github_api.issues if i), None)  # pragma: no branch

    assert issue.labels == ["internal"]
    assert issue.org == "ebmdatalab"
    assert issue.repo == "opensafely-output-review"
    assert issue.title == "test-workspace 01AAA1AAAAAAA1AAAAA11A1AAA"

    lines = issue.body.split("\n")
    assert user.name in lines[0]
    assert lines[1] == "Release request ID: 01AAA1AAAAAAA1AAAAA11A1AAA"
    assert workspace.repo.name in lines[2]
    assert workspace.name in lines[3]


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

    issue = next((i for i in github_api.closed_issues if i), None)  # pragma: no branch

    assert issue.org == "ebmdatalab"
    assert issue.repo == "opensafely-output-review"
    assert issue.title_text == "01AAA1AAAAAAA1AAAAA11A1AAA"
    assert issue.comment == f"Issue closed: Closed for reasons by {user.username}"

    comment = next((c for c in github_api.comments if c), None)  # pragma: no branch
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
            ["file added (filegroup 'Group 1') by user test"],
            "ebmdatalab",
            "opensafely-output-review",
            github_api,
            notify_slack=False,
        )
        == "http://example.com/issues/comment"
    )

    comment = next((c for c in github_api.comments if c), None)  # pragma: no branch
    assert comment.org == "ebmdatalab"
    assert comment.repo == "opensafely-output-review"
    assert comment.title_text == "01AAA1AAAAAAA1AAAAA11A1AAA"
    assert (
        comment.body
        == "Release request updated:\n- file added (filegroup 'Group 1') by user test"
    )
    assert slack_messages == []


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
            ["request resubmitted by user test"],
            "ebmdatalab",
            "opensafely-output-review",
            github_api,
            notify_slack=True,
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
