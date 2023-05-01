from django.conf import settings

from jobserver.issues import _size_formatter, create_output_checking_request

from ...factories import OrgFactory, OrgMembershipFactory, UserFactory


def test_size_formatter_bytes():
    assert _size_formatter(0) == "0b"
    assert _size_formatter(742) == "742b"


def test_size_formatter_kilobytes():
    assert _size_formatter(1024) == "1.0Kb"
    assert _size_formatter(1400) == "1.37Kb"


def test_size_formatter_megabytes():
    assert _size_formatter(1048576) == "1.0Mb"
    assert _size_formatter(1600000) == "1.53Mb"


def test_create_github_issue_external_success(build_release_with_files):
    release = build_release_with_files(["file1.txt", "graph.png"])

    class CapturingAPI:
        def create_issue(self, org, repo, title, body, labels):
            # capture all the values so they can interrogated later
            self.org = org
            self.repo = repo
            self.title = title
            self.body = body
            self.labels = labels

    issue = CapturingAPI()

    create_output_checking_request(release, github_api=issue)

    assert issue.title == release.workspace.name

    # check we have URLs to everything
    assert settings.BASE_URL in issue.body
    assert release.created_by.get_staff_url() in issue.body
    assert release.get_absolute_url() in issue.body
    assert release.workspace.get_absolute_url() in issue.body

    # check dedent worked as expected
    assert not issue.body.startswith(" "), issue.body


def test_create_github_issue_internal_success(build_release_with_files):
    org = OrgFactory(slug="datalab")
    user = UserFactory()
    OrgMembershipFactory(org=org, user=user)
    release = build_release_with_files(["file1.txt", "graph.png"], created_by=user)

    class CapturingAPI:
        def create_issue(self, org, repo, title, body, labels):
            # capture all the values so they can interrogated later
            self.org = org
            self.repo = repo
            self.title = title
            self.body = body
            self.labels = labels

    issue = CapturingAPI()

    create_output_checking_request(release, github_api=issue)

    assert issue.title == release.workspace.name

    # check we have URLs to everything
    assert settings.BASE_URL in issue.body
    assert release.created_by.get_staff_url() in issue.body
    assert release.get_absolute_url() in issue.body
    assert release.workspace.get_absolute_url() in issue.body

    # check dedent worked as expected
    assert not issue.body.startswith(" ")
