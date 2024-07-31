from django.conf import settings

from jobserver.issues import (
    _size_formatter,
    create_copilot_publish_report_request,
    create_output_checking_request,
)

from ...factories import (
    OrgFactory,
    OrgMembershipFactory,
    ProjectFactory,
    PublishRequestFactory,
    ReportFactory,
    UserFactory,
)


def test_size_formatter_bytes():
    assert _size_formatter(0) == "0b"
    assert _size_formatter(742) == "742b"


def test_size_formatter_kilobytes():
    assert _size_formatter(1024) == "1.0Kb"
    assert _size_formatter(1400) == "1.37Kb"


def test_size_formatter_megabytes():
    assert _size_formatter(1048576) == "1.0Mb"
    assert _size_formatter(1600000) == "1.53Mb"


def test_create_copilot_publish_report_request(github_api):
    project = ProjectFactory(copilot=UserFactory())
    report = ReportFactory(project=project, title="Test report")
    publish_request = PublishRequestFactory()
    publish_request.snapshot.files.add(report.release_file)

    create_copilot_publish_report_request(report, github_api)

    issue = next((i for i in github_api.issues if i), None)  # pragma: no branch

    assert issue.labels == ["publication-copiloted"]
    assert issue.org == "ebmdatalab"
    assert issue.repo == "publications-copiloted"
    assert issue.title == f"OSI Report: {report.title}"

    lines = issue.body.split("\n")

    assert lines[0] == "### Report details"

    assert lines[1].endswith(report.project.copilot.name)
    assert lines[2].endswith(report.project.get_staff_url())
    assert lines[3].endswith(report.get_absolute_url())
    assert report.get_staff_url() in issue.body


def test_create_github_issue_external_success(build_release_with_files, github_api):
    release = build_release_with_files(["file1.txt", "graph.png"])

    create_output_checking_request(release, github_api=github_api)

    issue = next((i for i in github_api.issues if i), None)  # pragma: no branch

    assert issue.title == release.workspace.name

    lines = issue.body.split("\n")

    assert release.created_by.name in lines[0]
    assert release.created_by.get_staff_url() in lines[0]

    assert release.id in lines[1]
    assert release.get_absolute_url() in lines[1]

    assert release.workspace.repo.name in lines[2]
    assert release.workspace.repo.url in lines[2]

    assert release.workspace.name in lines[3]
    assert release.workspace.get_absolute_url() in lines[3]

    assert lines[5].startswith(str(release.files.count()))

    assert lines[7].startswith("[Review request form]()")

    assert lines[9].startswith("**When you start")

    # check dedent worked as expected
    assert not issue.body.startswith(" "), issue.body


def test_create_github_issue_internal_success(build_release_with_files, github_api):
    org = OrgFactory(pk=settings.BENNETT_ORG_PK)
    user = UserFactory()
    OrgMembershipFactory(org=org, user=user)
    release = build_release_with_files(["file1.txt", "graph.png"], created_by=user)

    create_output_checking_request(release, github_api=github_api)

    issue = next((i for i in github_api.issues if i), None)  # pragma: no branch

    assert issue.title == release.workspace.name

    lines = issue.body.split("\n")

    assert release.created_by.name in lines[0]
    assert release.created_by.get_staff_url() in lines[0]

    assert release.id in lines[1]
    assert release.get_absolute_url() in lines[1]

    assert release.workspace.repo.name in lines[2]
    assert release.workspace.repo.url in lines[2]

    assert release.workspace.name in lines[3]
    assert release.workspace.get_absolute_url() in lines[3]

    assert lines[5].startswith(str(release.files.count()))

    assert lines[7] == ""

    assert lines[9].startswith("**When you start")

    # check dedent worked as expected
    assert not issue.body.startswith(" ")
