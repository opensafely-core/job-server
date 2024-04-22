from django.conf import settings
from first import first

from airlock.issues import create_output_checking_issue
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
            workspace, "01AAA1AAAAAAA1AAAAA11A1AAA", user, github_api
        )
        == "http://example.com"
    )

    issue = first(github_api.issues)

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
            workspace, "01AAA1AAAAAAA1AAAAA11A1AAA", user, github_api
        )
        == "http://example.com"
    )

    issue = first(github_api.issues)

    assert issue.labels == ["internal"]
    assert issue.org == "ebmdatalab"
    assert issue.repo == "opensafely-output-review"
    assert issue.title == "test-workspace 01AAA1AAAAAAA1AAAAA11A1AAA"

    lines = issue.body.split("\n")
    assert user.name in lines[0]
    assert lines[1] == "Release request ID: 01AAA1AAAAAAA1AAAAA11A1AAA"
    assert workspace.repo.name in lines[2]
    assert workspace.name in lines[3]
