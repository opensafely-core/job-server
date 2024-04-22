import json
import random
import string

import pytest
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from jobserver.api.releases import (
    Level4AuthorisationAPI,
    Level4TokenAuthenticationAPI,
    ReleaseAPI,
    ReleaseFileAPI,
    ReleaseNotificationAPICreate,
    ReleaseWorkspaceAPI,
    ReviewAPI,
    SnapshotAPI,
    SnapshotCreateAPI,
    SnapshotPublishAPI,
    WorkspaceStatusAPI,
    is_interactive_report,
    validate_release_access,
    validate_upload_access,
)
from jobserver.authorization import (
    CoreDeveloper,
    OutputChecker,
    ProjectCollaborator,
    permissions,
)
from jobserver.commands.users import generate_login_token
from jobserver.models import (
    PublishRequest,
    Release,
    ReleaseFileReview,
)
from jobserver.utils import set_from_qs
from tests.factories import (
    AnalysisRequestFactory,
    BackendFactory,
    BackendMembershipFactory,
    JobRequestFactory,
    ProjectFactory,
    PublishRequestFactory,
    ReleaseFactory,
    ReleaseFileFactory,
    SnapshotFactory,
    UserFactory,
    UserSocialAuthFactory,
    WorkspaceFactory,
)
from tests.fakes import FakeGitHubAPI


def test_is_interactive_report_no_match():
    # not 3 parts
    assert is_interactive_report(ReleaseFileFactory(name="no_match")) is None

    # starts with output but not endswith report.html
    assert is_interactive_report(ReleaseFileFactory(name="output/foo/file.txt")) is None

    # ends with report.html but does not start with output
    assert (
        is_interactive_report(ReleaseFileFactory(name="other/foo/report.txt")) is None
    )

    # no analysis request with id foo exists
    assert (
        is_interactive_report(ReleaseFileFactory(name="output/foo/report.html")) is None
    )


def test_is_interactive_report_matches():
    AnalysisRequestFactory.create(id="foo")
    assert (
        is_interactive_report(ReleaseFileFactory(name="output/foo/report.html"))
        is not None
    )


def test_releaseapi_get_unknown_release(api_rf):
    request = api_rf.get("/")

    response = ReleaseAPI.as_view()(request, release_id="")

    assert response.status_code == 404


def test_releaseapi_get_with_anonymous_user(api_rf):
    release = ReleaseFactory()

    request = api_rf.get("/")

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 403


def test_releaseapi_get_with_permission(
    api_rf, build_release_with_files, project_membership
):
    release = build_release_with_files(["file.txt"])
    rfile = release.files.first()

    project_membership(
        user=release.created_by,
        project=release.workspace.project,
        roles=[ProjectCollaborator],
    )

    request = api_rf.get("/")
    request.user = release.created_by

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 200

    rfile = release.files.first()
    assert response.data == {
        "files": [
            {
                "name": "file.txt",
                "id": rfile.pk,
                "url": f"/api/v2/releases/file/{rfile.id}",
                "user": rfile.created_by.username,
                "date": rfile.created_at.isoformat(),
                "size": rfile.size,
                "sha256": rfile.filehash,
                "is_deleted": False,
                "backend": release.backend.name,
                "metadata": None,
                "review": None,
            }
        ],
    }


def test_releaseapi_get_without_permission(api_rf):
    release = ReleaseFactory()

    request = api_rf.get("/")
    request.user = UserFactory()

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 403


def test_releaseapi_post_already_uploaded(api_rf, build_release_with_files):
    user = UserFactory(roles=[OutputChecker])
    release = build_release_with_files(["file.txt"])

    BackendMembershipFactory(backend=release.backend, user=user)

    count_before = release.files.count()

    request = api_rf.post(
        "/",
        content_type="application/octet-stream",
        data="test",
        headers={
            "content-disposition": "attachment; filename=file.txt",
            "authorization": release.backend.auth_token,
            "os-user": user.username,
        },
    )

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 400
    assert "file.txt" in response.data["detail"]
    assert "already been uploaded" in response.data["detail"]
    assert release.files.count() == count_before


def test_releaseapi_post_bad_backend(api_rf, build_release, file_content):
    user = UserFactory(roles=[OutputChecker])
    release = build_release(["output/file.txt"])

    bad_backend = BackendFactory()
    BackendMembershipFactory(backend=bad_backend, user=user)

    content = "".join(random.choice(string.ascii_letters) for i in range(10))
    content = content.encode("utf8")
    request = api_rf.post(
        "/",
        content_type="application/octet-stream",
        data=file_content,
        headers={
            "content-disposition": "attachment; filename=output/file.txt",
            "authorization": bad_backend.auth_token,
            "os-user": user.username,
        },
    )

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 400
    assert bad_backend.slug in response.data["detail"]


def test_releaseapi_post_bad_backend_token(api_rf):
    release = ReleaseFactory()

    request = api_rf.post("/", headers={"authorization": "invalid"})

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 403


def test_releaseapi_post_bad_filename(api_rf, build_release, file_content):
    user = UserFactory(roles=[OutputChecker])
    release = build_release(["file.txt"])

    BackendMembershipFactory(backend=release.backend, user=user)

    content = "".join(random.choice(string.ascii_letters) for i in range(10))
    content = content.encode("utf8")
    request = api_rf.post(
        "/",
        content_type="application/octet-stream",
        data=file_content,
        headers={
            "content-disposition": "attachment; filename=wrongname.txt",
            "authorization": release.backend.auth_token,
            "os-user": user.username,
        },
    )

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 400
    assert "wrongname.txt" in response.data["detail"]


def test_releaseapi_post_bad_user(api_rf):
    release = ReleaseFactory()

    request = api_rf.post(
        "/",
        headers={
            "authorization": release.backend.auth_token,
            "os-user": "baduser",
        },
    )

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 403


def test_releaseapi_post_no_files(api_rf):
    user = UserFactory(roles=[OutputChecker])
    release = ReleaseFactory()

    BackendMembershipFactory(backend=release.backend, user=user)

    request = api_rf.post(
        "/",
        headers={
            "content-disposition": "attachment; filename=file1.txt",
            "authorization": release.backend.auth_token,
            "os-user": user.username,
        },
    )

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 400
    assert "No data" in response.data["detail"]


def test_releaseapi_post_no_user(api_rf):
    release = ReleaseFactory()

    request = api_rf.post(
        "/",
        headers={
            "authorization": release.backend.auth_token,
        },
    )

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 403


def test_releaseapi_post_success(api_rf, slack_messages, build_release, file_content):
    creating_user = UserFactory()
    uploading_user = UserFactory(roles=[OutputChecker])
    backend = BackendFactory(name="test-backend")

    release = build_release(["file.txt"], backend=backend, created_by=creating_user)

    BackendMembershipFactory(backend=release.backend, user=creating_user)
    BackendMembershipFactory(backend=release.backend, user=uploading_user)

    request = api_rf.post(
        "/",
        content_type="application/octet-stream",
        data=file_content,
        headers={
            "content-disposition": "attachment; filename=file.txt",
            "authorization": release.backend.auth_token,
            "os-user": uploading_user.username,
        },
    )

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    rfile = release.files.first()
    assert response.status_code == 201, response.data
    assert response.headers["Location"].endswith(f"/releases/file/{rfile.id}")
    assert response.headers["File-Id"] == rfile.id

    assert len(slack_messages) == 1
    text, channel = slack_messages[0]
    assert channel == "opensafely-releases"
    assert f"{uploading_user.get_staff_url()}|{uploading_user.name}>" in text
    assert f"{release.get_absolute_url()}|release>" in text
    assert f"{rfile.get_absolute_url()}|{rfile.name}>" in text
    assert release.backend.name in text


def test_releaseapi_post_success_for_analysis_request(
    api_rf, slack_messages, build_release, file_content
):
    creating_user = UserFactory()
    uploading_user = UserFactory(roles=[OutputChecker])
    backend = BackendFactory(name="test-backend")

    job_request = JobRequestFactory(created_by=creating_user)
    analysis_request = AnalysisRequestFactory(
        created_by=creating_user,
        job_request=job_request,
        report_title="report title",
    )

    assert not analysis_request.report

    filename = f"output/{analysis_request.pk}/report.html"

    release = build_release([filename], backend=backend, created_by=creating_user)

    BackendMembershipFactory(backend=release.backend, user=creating_user)
    BackendMembershipFactory(backend=release.backend, user=uploading_user)

    request = api_rf.post(
        "/",
        content_type="application/octet-stream",
        data=file_content,
        headers={
            "content-disposition": f"attachment; filename={filename}",
            "authorization": release.backend.auth_token,
            "os-user": uploading_user.username,
        },
    )

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    rfile = release.files.first()
    assert response.status_code == 201, response.data
    assert response.headers["Location"].endswith(f"/releases/file/{rfile.id}")
    assert response.headers["File-Id"] == rfile.id

    assert len(slack_messages) == 2

    text, channel = slack_messages[0]
    assert channel == "opensafely-releases"
    assert f"{uploading_user.get_staff_url()}|{uploading_user.name}>" in text
    assert f"{release.get_absolute_url()}|release>" in text
    assert f"{rfile.get_absolute_url()}|{rfile.name}>" in text
    assert release.backend.name in text

    text, channel = slack_messages[1]
    assert channel == "interactive-requests"
    assert analysis_request.report_title in text
    assert analysis_request.get_absolute_url() in text

    analysis_request.refresh_from_db()
    assert analysis_request.report
    assert analysis_request.report.title == analysis_request.report_title
    assert analysis_request.report.description == ""
    assert analysis_request.report.created_by == analysis_request.created_by


def test_releaseapi_post_success_for_html_not_linked_to_an_analysis_request(
    api_rf, slack_messages, build_release, file_content
):
    """
    Test the ReleaseAPI post handler with an HTML file

    We need to split up the "is HTML file AND name matches an AnalysisRequest"
    conditional so that we can deal with TimeflakePrimaryKeyBinary raising
    ValidationErrors for invalid input, as opposed to ObjectDoesNotExist.

    Once that is fixed we can remove this test and coverage should still
    be appeased.
    """
    creating_user = UserFactory()
    uploading_user = UserFactory(roles=[OutputChecker])
    backend = BackendFactory(name="test-backend")

    release = build_release(["file.html"], backend=backend, created_by=creating_user)

    BackendMembershipFactory(backend=release.backend, user=creating_user)
    BackendMembershipFactory(backend=release.backend, user=uploading_user)

    request = api_rf.post(
        "/",
        content_type="application/octet-stream",
        data=file_content,
        headers={
            "content-disposition": "attachment; filename=file.html",
            "authorization": release.backend.auth_token,
            "os-user": uploading_user.username,
        },
    )

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    rfile = release.files.first()
    assert response.status_code == 201, response.data
    assert response.headers["Location"].endswith(f"/releases/file/{rfile.id}")
    assert response.headers["File-Id"] == rfile.id

    assert len(slack_messages) == 1
    text, channel = slack_messages[0]
    assert channel == "opensafely-releases"
    assert f"{uploading_user.get_staff_url()}|{uploading_user.name}>" in text
    assert f"{release.get_absolute_url()}|release>" in text
    assert f"{rfile.get_absolute_url()}|{rfile.name}>" in text
    assert release.backend.name in text


def test_releaseapi_post_with_content_length_too_large(api_rf, build_release, settings):
    settings.RELEASE_FILE_SIZE_LIMIT = 5

    creating_user = UserFactory()
    uploading_user = UserFactory(roles=[OutputChecker])
    backend = BackendFactory(name="test-backend")

    release = build_release(["file.txt"], backend=backend, created_by=creating_user)

    BackendMembershipFactory(backend=release.backend, user=creating_user)
    BackendMembershipFactory(backend=release.backend, user=uploading_user)

    request = api_rf.post(
        "/",
        content_type="application/octet-stream",
        data="test",
        headers={
            "content-disposition": "attachment; filename=file.txt",
            "content-length": "42",
            "authorization": release.backend.auth_token,
            "os-user": uploading_user.username,
        },
    )

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 400, response.data

    # this is not actually 0, but 5 bytes translated to Mb appears as 0.0.
    assert response.data[0] == "File is too large, it must be below 0.0Mb"


def test_releaseapi_post_with_file_size_too_large(
    api_rf, build_release, file_content, settings
):
    settings.RELEASE_FILE_SIZE_LIMIT = 5

    creating_user = UserFactory()
    uploading_user = UserFactory(roles=[OutputChecker])
    backend = BackendFactory(name="test-backend")

    release = build_release(["file.txt"], backend=backend, created_by=creating_user)

    BackendMembershipFactory(backend=release.backend, user=creating_user)
    BackendMembershipFactory(backend=release.backend, user=uploading_user)

    request = api_rf.post(
        "/",
        content_type="application/octet-stream",
        data=file_content,
        headers={
            "content-disposition": "attachment; filename=file.txt",
            "authorization": release.backend.auth_token,
            "os-user": uploading_user.username,
        },
    )

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 400, response.data

    # this is not actually 0, but 5 bytes translated to Mb appears as 0.0.
    assert response.data[0] == "File is too large, it must be below 0.0Mb"


def test_releaseapi_post_unknown_release(api_rf):
    request = api_rf.post("/")

    response = ReleaseAPI.as_view()(request, release_id="")

    assert response.status_code == 404


def test_releaseapi_post_with_no_backend_token(api_rf):
    release = ReleaseFactory()

    request = api_rf.post("/")

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 403


def test_releasenotificationapicreate_success(api_rf, slack_messages):
    backend = BackendFactory(name="test")

    data = {
        "created_by": "test user",
        "path": "/path/to/outputs",
    }
    request = api_rf.post("/", data, headers={"authorization": backend.auth_token})
    request.user = UserFactory()

    response = ReleaseNotificationAPICreate.as_view()(request)

    assert response.status_code == 201, response.data

    # check we called the slack API in the expected way
    assert len(slack_messages) == 1
    text, channel = slack_messages[0]
    assert channel == "opensafely-releases"
    assert text == f"test user released outputs from /path/to/outputs on {backend.name}"


def test_releasenotificationapicreate_success_with_files(api_rf, slack_messages):
    backend = BackendFactory(name="test")

    data = {
        "created_by": "test user",
        "path": "/path/to/outputs",
        "files": ["output/file1.txt", "output/file2.txt"],
    }
    request = api_rf.post("/", data, headers={"authorization": backend.auth_token})
    request.user = UserFactory()

    response = ReleaseNotificationAPICreate.as_view()(request)

    assert response.status_code == 201, response.data

    # check we called the slack API in the expected way
    assert len(slack_messages) == 1
    text, channel = slack_messages[0]
    assert channel == "opensafely-releases"
    assert text == (
        f"test user released 2 outputs from /path/to/outputs on {backend.name}:\n"
        "`output/file1.txt`\n"
        "`output/file2.txt`"
    )


def test_releaseworkspaceapi_get_unknown_workspace(api_rf):
    request = api_rf.get("/")

    response = ReleaseWorkspaceAPI.as_view(get_github_api=FakeGitHubAPI)(
        request, workspace_name=""
    )

    assert response.status_code == 404


def test_releaseworkspaceapi_get_with_anonymous_user(api_rf):
    workspace = WorkspaceFactory()

    request = api_rf.get("/")

    response = ReleaseWorkspaceAPI.as_view(get_github_api=FakeGitHubAPI)(
        request, workspace_name=workspace.name
    )

    assert response.status_code == 403


def test_releaseworkspaceapi_get_with_permission(
    api_rf, build_release_with_files, project_membership
):
    workspace = WorkspaceFactory()
    backend1 = BackendFactory(slug="backend1")
    backend2 = BackendFactory(slug="backend2")
    user = UserFactory()
    project_membership(
        user=user, project=workspace.project, roles=[ProjectCollaborator]
    )

    # two release for same filename but different content
    release1 = build_release_with_files(
        ["file1.txt"], workspace=workspace, backend=backend1, created_by=user
    )
    rfile1 = release1.files.first()
    release2 = build_release_with_files(
        ["file1.txt"], workspace=workspace, backend=backend2, created_by=user
    )
    rfile2 = release2.files.first()

    request = api_rf.get("/")
    request.user = user

    response = ReleaseWorkspaceAPI.as_view(get_github_api=FakeGitHubAPI)(
        request, workspace_name=workspace.name
    )

    assert response.status_code == 200
    assert response.data == {
        "files": [
            {
                "name": "backend2/file1.txt",
                "id": rfile2.pk,
                "url": f"/api/v2/releases/file/{rfile2.id}",
                "user": rfile2.created_by.username,
                "date": rfile2.created_at.isoformat(),
                "size": rfile2.size,
                "sha256": rfile2.filehash,
                "is_deleted": False,
                "backend": release2.backend.name,
                "metadata": None,
                "review": None,
            },
            {
                "name": "backend1/file1.txt",
                "id": rfile1.pk,
                "url": f"/api/v2/releases/file/{rfile1.id}",
                "user": rfile1.created_by.username,
                "date": rfile1.created_at.isoformat(),
                "size": rfile1.size,
                "sha256": rfile1.filehash,
                "is_deleted": False,
                "backend": release1.backend.name,
                "metadata": None,
                "review": None,
            },
        ],
    }


def test_releaseworkspaceapi_get_without_permission(api_rf):
    workspace = WorkspaceFactory()

    request = api_rf.get("/")
    request.user = UserFactory()

    response = ReleaseWorkspaceAPI.as_view(get_github_api=FakeGitHubAPI)(
        request, workspace_name=workspace.name
    )

    assert response.status_code == 403


def test_releaseworkspaceapi_post_create_release(
    api_rf, slack_messages, project_membership
):
    user = UserFactory(roles=[OutputChecker])
    workspace = WorkspaceFactory()
    project_membership(user=user, project=workspace.project)

    backend = BackendFactory(auth_token="test", name="test-backend")
    BackendMembershipFactory(backend=backend, user=user)

    assert Release.objects.count() == 0

    data = {
        "files": [
            {
                "name": "file1.txt",
                "url": "url",
                "size": 7,
                "sha256": "hash",
                "date": timezone.now(),
                "metadata": {},
                "review": None,
            }
        ],
        "metadata": {},
        "review": None,
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

    response = ReleaseWorkspaceAPI.as_view(get_github_api=FakeGitHubAPI)(
        request, workspace_name=workspace.name
    )

    assert response.status_code == 201, response.data
    assert Release.objects.count() == 1

    release = Release.objects.first()
    assert response["Release-Id"] == str(release.id)
    assert response.data["release_id"] == str(release.id)
    assert response.data["release_url"].startswith("http://testserver/")
    assert response.data["release_url"].endswith(f"/releases/{release.id}/")

    assert len(slack_messages) == 1
    text, channel = slack_messages[0]

    assert channel == "opensafely-releases"
    assert f"{user.get_staff_url()}|{user.name}>" in text
    assert f"{release.get_absolute_url()}|release>" in text
    assert f"{workspace.get_absolute_url()}|{workspace.name}>" in text
    assert backend.name in text


def test_releaseworkspaceapi_post_create_release_with_airlock_id(
    api_rf, slack_messages, project_membership
):
    user = UserFactory(roles=[OutputChecker])
    workspace = WorkspaceFactory()
    project_membership(user=user, project=workspace.project)

    backend = BackendFactory(auth_token="test", name="test-backend")
    BackendMembershipFactory(backend=backend, user=user)

    assert Release.objects.count() == 0

    airlock_metadata = {"tool": "airlock", "airlock_id": "01AAA1AAAAAAA1AAAAA11A1AAA"}
    data = {
        "files": [
            {
                "name": "file1.txt",
                "url": "url",
                "size": 7,
                "sha256": "hash",
                "date": timezone.now(),
                "metadata": airlock_metadata,
                "review": None,
            }
        ],
        "metadata": airlock_metadata,
        "review": None,
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

    response = ReleaseWorkspaceAPI.as_view(get_github_api=FakeGitHubAPI)(
        request, workspace_name=workspace.name
    )

    assert response.status_code == 201, response.data
    assert Release.objects.count() == 1

    release = Release.objects.first()
    assert release.id == airlock_metadata["airlock_id"]
    assert response["Release-Id"] == airlock_metadata["airlock_id"]
    assert response.data["release_id"] == airlock_metadata["airlock_id"]


def test_releaseworkspaceapi_post_create_release_with_oversized_file(
    api_rf, project_membership
):
    user = UserFactory(roles=[OutputChecker])
    workspace = WorkspaceFactory()
    project_membership(user=user, project=workspace.project)

    backend = BackendFactory(auth_token="test", name="test-backend")
    BackendMembershipFactory(backend=backend, user=user)

    data = {
        "files": [
            {
                "name": "file1.txt",
                "url": "url",
                "size": 16777217,
                "sha256": "hash",
                "date": timezone.now(),
                "metadata": {},
                "review": None,
            }
        ],
        "metadata": {},
        "review": None,
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

    response = ReleaseWorkspaceAPI.as_view(get_github_api=FakeGitHubAPI)(
        request, workspace_name=workspace.name
    )

    assert response.status_code == 400, response.data
    assert response.data["files"][0]["size"][0].startswith("File size should be <16Mb.")


def test_releaseworkspaceapi_post_release_already_exists(api_rf, project_membership):
    user = UserFactory(roles=[OutputChecker])

    release = ReleaseFactory()
    rfile = ReleaseFileFactory(
        release=release,
        created_by=user,
        name="file.txt",
        filehash="hash",
    )

    BackendMembershipFactory(backend=release.backend, user=user)
    project_membership(project=release.workspace.project, user=user)

    data = {
        "files": [
            {
                "name": rfile.name,
                "url": "url",
                "size": 7,
                "sha256": rfile.filehash,
                "date": timezone.now(),
                "metadata": {},
                "review": None,
            }
        ],
        "metadata": {},
        "review": {},
    }
    request = api_rf.post(
        "/",
        data=data,
        format="json",
        headers={
            "authorization": release.backend.auth_token,
            "os-user": user.username,
        },
    )

    response = ReleaseWorkspaceAPI.as_view(get_github_api=FakeGitHubAPI)(
        request, workspace_name=release.workspace.name
    )

    assert response.status_code == 400
    assert "file.txt" in response.data["detail"]
    assert "already been uploaded" in response.data["detail"]


def test_releaseworkspaceapi_post_unknown_workspace(api_rf):
    request = api_rf.post("/")

    response = ReleaseWorkspaceAPI.as_view(get_github_api=FakeGitHubAPI)(
        request, workspace_name=""
    )

    assert response.status_code == 404


def test_releaseworkspaceapi_post_with_bad_backend_token(api_rf):
    workspace = WorkspaceFactory()
    BackendFactory(auth_token="test")

    request = api_rf.post("/", headers={"authorization": "invalid"})

    response = ReleaseWorkspaceAPI.as_view(get_github_api=FakeGitHubAPI)(
        request, workspace_name=workspace.name
    )

    assert response.status_code == 403


def test_releaseworkspaceapi_post_with_bad_json(api_rf, project_membership):
    user = UserFactory(roles=[OutputChecker])
    workspace = WorkspaceFactory()
    project_membership(user=user, project=workspace.project)

    backend = BackendFactory(auth_token="test")
    BackendMembershipFactory(backend=backend, user=user)

    request = api_rf.post(
        "/",
        content_type="application/json",
        data=json.dumps({}),
        headers={
            "content-disposition": "attachment; filename=release.zip",
            "authorization": "test",
            "os-user": user.username,
        },
    )

    response = ReleaseWorkspaceAPI.as_view(get_github_api=FakeGitHubAPI)(
        request, workspace_name=workspace.name
    )

    assert response.status_code == 400


def test_releaseworkspaceapi_post_with_bad_user(api_rf):
    workspace = WorkspaceFactory()
    BackendFactory(auth_token="test")

    request = api_rf.post(
        "/",
        headers={
            "authorization": "test",
            "os-user": "baduser",
        },
    )

    response = ReleaseWorkspaceAPI.as_view(get_github_api=FakeGitHubAPI)(
        request, workspace_name=workspace.name
    )

    assert response.status_code == 403


def test_releaseworkspaceapi_post_without_backend_token(api_rf):
    workspace = WorkspaceFactory()

    request = api_rf.post("/")

    response = ReleaseWorkspaceAPI.as_view(get_github_api=FakeGitHubAPI)(
        request, workspace_name=workspace.name
    )

    assert response.status_code == 403


def test_releaseworkspaceapi_post_without_user(api_rf):
    workspace = WorkspaceFactory()
    BackendFactory(auth_token="test")

    request = api_rf.post("/", headers={"authorization": "test"})

    response = ReleaseWorkspaceAPI.as_view(get_github_api=FakeGitHubAPI)(
        request, workspace_name=workspace.name
    )

    assert response.status_code == 403


def test_releasefileapi_get_unknown_file(api_rf):
    request = api_rf.get("/")

    response = ReleaseFileAPI.as_view()(request, file_id="")

    assert response.status_code == 404


def test_releasefileapi_with_anonymous_user(api_rf):
    rfile = ReleaseFileFactory()

    request = api_rf.get("/")

    response = ReleaseFileAPI.as_view()(request, file_id=rfile.id)

    assert response.status_code == 403


def test_releasefileapi_with_deleted_file(api_rf, project_membership):
    rfile = ReleaseFileFactory(deleted_at=timezone.now(), deleted_by=UserFactory())
    user = UserFactory()

    project_membership(
        user=user,
        project=rfile.release.workspace.project,
        roles=[ProjectCollaborator],
    )

    request = api_rf.get("/")
    request.user = user

    response = ReleaseFileAPI.as_view()(request, file_id=rfile.id)

    assert response.status_code == 404, response.data


def test_releasefileapi_with_no_file_on_disk(api_rf, build_release, project_membership):
    release = build_release(["file1.txt"])
    rfile = ReleaseFileFactory(
        release=release,
        workspace=release.workspace,
        name="file1.txt",
        uploaded_at=None,
    )
    user = UserFactory()

    project_membership(
        user=user,
        project=release.workspace.project,
        roles=[ProjectCollaborator],
    )

    request = api_rf.get("/")
    request.user = user

    response = ReleaseFileAPI.as_view()(request, file_id=rfile.id)

    assert response.status_code == 200, response.data
    assert response.data == "File not yet uploaded"


def test_releasefileapi_with_nginx_redirect(
    api_rf, build_release_with_files, project_membership
):
    release = build_release_with_files(["file.txt"])
    rfile = release.files.first()
    user = UserFactory()

    # test nginx configuration
    project_membership(
        user=user,
        project=release.workspace.project,
        roles=[ProjectCollaborator],
    )

    request = api_rf.get("/", headers={"releases-redirect": "/storage"})
    request.user = user

    response = ReleaseFileAPI.as_view()(request, file_id=rfile.id)

    assert response.status_code == 200
    assert (
        response.headers["X-Accel-Redirect"]
        == f"/storage/{release.workspace.name}/releases/{release.id}/file.txt"
    )


def test_releasefileapi_with_permission(
    api_rf, build_release_with_files, project_membership
):
    release = build_release_with_files(["file1.txt"])
    rfile = release.files.first()
    user = UserFactory()

    # logged in, with permission
    project_membership(
        user=user,
        project=release.workspace.project,
        roles=[ProjectCollaborator],
    )

    request = api_rf.get("/")
    request.user = user

    response = ReleaseFileAPI.as_view()(request, file_id=rfile.id)

    assert response.status_code == 200
    assert b"".join(response.streaming_content) == rfile.absolute_path().read_bytes()
    assert response.headers["Content-Type"] == "text/plain; charset=utf-8"


def test_releasefileapi_without_permission(api_rf):
    rfile = ReleaseFileFactory()

    request = api_rf.get("/")
    request.user = UserFactory()  # logged in, but no permission

    response = ReleaseFileAPI.as_view()(request, file_id=rfile.id)

    assert response.status_code == 403


def test_reviewapi_without_permission(api_rf):
    release = ReleaseFactory()

    data = {
        "files": [],
        "metadata": {},
        "review": {},
    }
    request = api_rf.post("/", data=data, format="json")

    response = ReviewAPI.as_view()(request, release_id=release.pk)

    assert response.status_code == 200, response.data


def test_reviewapi_unknown_filename_or_content(api_rf):
    release = ReleaseFactory()
    ReleaseFileFactory(release=release, name="test1", filehash="test1")
    ReleaseFileFactory(release=release, name="test2", filehash="test2")

    data = {
        "files": [
            {
                "name": "unknown",
                "url": "url",
                "size": 7,
                "sha256": "test1",
                "date": timezone.now(),
                "metadata": {},
                "review": {
                    "status": "APPROVED",
                    "comments": {"test": "foo"},
                },
            },
            {
                "name": "test2",
                "url": "url",
                "size": 7,
                "sha256": "unknown",
                "date": timezone.now(),
                "metadata": {},
                "review": {
                    "status": "REJECTED",
                    "comments": {"test": "bar"},
                },
            },
        ],
        "metadata": {},
        "review": {},
    }

    request = api_rf.post("/", data=data, format="json")
    request.user = UserFactory(roles=[OutputChecker])

    response = ReviewAPI.as_view()(request, release_id=release.pk)

    assert response.status_code == 400, response.data


def test_reviewapi_success(api_rf):
    release = ReleaseFactory()
    ReleaseFileFactory(release=release, name="test1", filehash="test1")
    ReleaseFileFactory(release=release, name="test2", filehash="test2")

    data = {
        "files": [
            {
                "name": "test1",
                "url": "url",
                "size": 7,
                "sha256": "test1",
                "date": timezone.now(),
                "metadata": {},
                "review": {
                    "status": "APPROVED",
                    "comments": {"test": "foo"},
                },
            },
            {
                "name": "test2",
                "url": "url",
                "size": 7,
                "sha256": "test2",
                "date": timezone.now(),
                "metadata": {},
                "review": {
                    "status": "REJECTED",
                    "comments": {"test": "bar"},
                },
            },
        ],
        "metadata": {},
        "review": {"foo": "bar"},
    }

    request = api_rf.post("/", data=data, format="json")
    request.user = UserFactory(roles=[OutputChecker])

    response = ReviewAPI.as_view()(request, release_id=release.pk)

    assert response.status_code == 200, response.data

    release.refresh_from_db()
    assert release.review == {"foo": "bar"}

    review1, review2 = ReleaseFileReview.objects.filter(
        release_file__release=release
    ).order_by("release_file__name")

    assert review1.status == "APPROVED"
    assert review1.comments == {"test": "foo"}

    assert review2.status == "REJECTED"
    assert review2.comments == {"test": "bar"}


def test_snapshotapi_published_with_anonymous_user(api_rf, time_machine):
    snapshot = SnapshotFactory()
    PublishRequestFactory(
        snapshot=snapshot,
        decision=PublishRequest.Decisions.APPROVED,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
    )

    request = api_rf.get("/")

    response = SnapshotAPI.as_view()(
        request,
        workspace_id=snapshot.workspace.name,
        snapshot_id=snapshot.pk,
    )

    assert response.status_code == 200
    assert response.data == {"files": []}


def test_snapshotapi_published_with_permission(api_rf):
    snapshot = SnapshotFactory()
    PublishRequestFactory(
        snapshot=snapshot,
        decision=PublishRequest.Decisions.APPROVED,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
    )
    user = UserFactory(roles=[ProjectCollaborator])

    request = api_rf.get("/")
    request.user = user

    response = SnapshotAPI.as_view()(
        request,
        workspace_id=snapshot.workspace.name,
        snapshot_id=snapshot.pk,
    )

    assert response.status_code == 200
    assert response.data == {"files": []}


def test_snapshotapi_published_without_permission(api_rf):
    snapshot = SnapshotFactory()
    PublishRequestFactory(
        snapshot=snapshot,
        decision=PublishRequest.Decisions.APPROVED,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
    )

    request = api_rf.get("/")
    request.user = UserFactory()  # logged in, but no permission

    response = SnapshotAPI.as_view()(
        request,
        workspace_id=snapshot.workspace.name,
        snapshot_id=snapshot.pk,
    )

    assert response.status_code == 200
    assert response.data == {"files": []}


def test_snapshotapi_unpublished_with_anonymous_user(api_rf):
    snapshot = SnapshotFactory()
    PublishRequestFactory(snapshot=snapshot)

    request = api_rf.get("/")

    response = SnapshotAPI.as_view()(
        request,
        workspace_id=snapshot.workspace.name,
        snapshot_id=snapshot.pk,
    )

    assert response.status_code == 403


def test_snapshotapi_unpublished_with_permission(api_rf):
    snapshot = SnapshotFactory()
    PublishRequestFactory(snapshot=snapshot)

    request = api_rf.get("/")
    request.user = UserFactory(roles=[ProjectCollaborator])

    response = SnapshotAPI.as_view()(
        request,
        workspace_id=snapshot.workspace.name,
        snapshot_id=snapshot.pk,
    )

    assert response.status_code == 200
    assert response.data == {"files": []}


def test_snapshotapi_unpublished_without_permission(api_rf):
    snapshot = SnapshotFactory()
    PublishRequestFactory(snapshot=snapshot)

    request = api_rf.get("/")
    request.user = UserFactory()  # logged in, but no permission

    response = SnapshotAPI.as_view()(
        request,
        workspace_id=snapshot.workspace.name,
        snapshot_id=snapshot.pk,
    )

    assert response.status_code == 403


def test_snapshotcreate_unknown_files(api_rf, project_membership, role_factory):
    workspace = WorkspaceFactory()
    user = UserFactory()
    project_membership(
        project=workspace.project,
        user=user,
        roles=[role_factory(permission=permissions.snapshot_create)],
    )

    request = api_rf.post("/", data={"file_ids": ["test"]})
    request.user = user

    response = SnapshotCreateAPI.as_view()(request, workspace_id=workspace.name)

    assert response.status_code == 400, response.data
    assert "Unknown file IDs" in response.data["detail"], response.data


def test_snapshotcreate_with_existing_snapshot(
    api_rf, build_release_with_files, project_membership, role_factory
):
    workspace = WorkspaceFactory()
    release = build_release_with_files(["file1.txt"], workspace=workspace)
    release.files.update(workspace=workspace)
    snapshot = SnapshotFactory(workspace=workspace)
    snapshot.files.set(release.files.all())

    user = UserFactory()
    project_membership(
        project=workspace.project,
        user=user,
        roles=[role_factory(permission=permissions.snapshot_create)],
    )

    request = api_rf.post("/", data={"file_ids": [release.files.first().pk]})
    request.user = user

    response = SnapshotCreateAPI.as_view()(request, workspace_id=workspace.name)

    assert response.status_code == 201, response.data
    assert response.data["url"] == snapshot.get_absolute_url()


def test_snapshotcreate_with_permission(
    api_rf, build_release_with_files, project_membership, role_factory
):
    workspace = WorkspaceFactory()
    release = build_release_with_files(
        [
            "file1.txt",
            "file2.txt",
            "file3.txt",
            "file4.txt",
            "file5.txt",
        ],
        workspace=workspace,
    )

    user = UserFactory()
    project_membership(
        project=workspace.project,
        user=user,
        roles=[role_factory(permission=permissions.snapshot_create)],
    )

    data = {
        "file_ids": [
            release.files.get(name="file1.txt").pk,
            release.files.get(name="file3.txt").pk,
            release.files.get(name="file5.txt").pk,
        ],
    }
    request = api_rf.post("/", data)
    request.user = user

    response = SnapshotCreateAPI.as_view()(request, workspace_id=workspace.name)

    assert response.status_code == 201

    workspace.refresh_from_db()

    assert workspace.snapshots.count() == 1

    snapshot_file_ids = set_from_qs(workspace.snapshots.first().files.all())
    current_file_ids = set_from_qs(workspace.files.all())
    assert snapshot_file_ids <= current_file_ids


def test_snapshotcreate_without_permission(api_rf):
    workspace = WorkspaceFactory()

    request = api_rf.post("/", data={"file_ids": ["test"]})
    request.user = UserFactory()

    response = SnapshotCreateAPI.as_view()(request, workspace_id=workspace.name)

    assert response.status_code == 403, response.data


def test_snapshotpublishapi_already_published(api_rf, role_factory):
    snapshot = SnapshotFactory()
    PublishRequestFactory(
        snapshot=snapshot,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
        decision=PublishRequest.Decisions.APPROVED,
    )

    assert snapshot.is_published

    request = api_rf.post("/")
    request.user = UserFactory(
        roles=[role_factory(permission=permissions.snapshot_publish)]
    )

    response = SnapshotPublishAPI.as_view()(
        request,
        workspace_id=snapshot.workspace.name,
        snapshot_id=snapshot.pk,
    )

    assert response.status_code == 200

    snapshot.refresh_from_db()
    assert snapshot.is_published


def test_snapshotpublishapi_success(api_rf, role_factory):
    snapshot = SnapshotFactory()
    PublishRequestFactory(snapshot=snapshot)

    assert snapshot.is_draft

    request = api_rf.post("/")
    request.user = UserFactory(
        roles=[role_factory(permission=permissions.snapshot_publish)]
    )

    response = SnapshotPublishAPI.as_view()(
        request,
        workspace_id=snapshot.workspace.name,
        snapshot_id=snapshot.pk,
    )

    assert response.status_code == 200

    snapshot.refresh_from_db()
    assert snapshot.is_published


def test_snapshotpublishapi_unknown_snapshot(api_rf, role_factory):
    workspace = WorkspaceFactory()

    request = api_rf.post("/")
    request.user = UserFactory(
        roles=[role_factory(permission=permissions.snapshot_publish)]
    )

    response = SnapshotPublishAPI.as_view()(
        request,
        workspace_id=workspace.name,
        snapshot_id=0,
    )

    assert response.status_code == 404


def test_snapshotpublishapi_with_missing_publish_request(api_rf, role_factory):
    snapshot = SnapshotFactory()

    request = api_rf.post("/")
    request.user = UserFactory(
        roles=[role_factory(permission=permissions.snapshot_publish)]
    )

    with pytest.raises(Exception, match="Snapshot is missing publish request"):
        SnapshotPublishAPI.as_view()(
            request,
            workspace_id=snapshot.workspace.name,
            snapshot_id=snapshot.pk,
        )


def test_snapshotpublishapi_without_permission(api_rf):
    snapshot = SnapshotFactory()

    request = api_rf.post("/")
    request.user = UserFactory()

    response = SnapshotPublishAPI.as_view()(
        request,
        workspace_id=snapshot.workspace.name,
        snapshot_id=snapshot.pk,
    )

    assert response.status_code == 403


def test_validate_release_access_with_auth_header_success(rf):
    user = UserFactory()
    workspace = WorkspaceFactory()

    token = user.rotate_token()

    request = rf.get("/", headers={"authorization": f"{user.username}:{token}"})
    request.user = AnonymousUser()

    assert validate_release_access(request, workspace) is None


def test_validate_release_access_with_auth_header_and_invalid_token(rf):
    user = UserFactory()
    workspace = WorkspaceFactory()

    # set a token so the user is considered a bot
    user.rotate_token()

    request = rf.get("/", headers={"authorization": f"{user.username}:invalid"})
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        validate_release_access(request, workspace)


def test_validate_release_access_with_auth_header_and_unknown_user(rf):
    user = UserFactory()
    workspace = WorkspaceFactory()

    token = user.rotate_token()

    request = rf.get("/", headers={"authorization": f"0:{token}"})
    request.user = AnonymousUser()

    with pytest.raises(NotAuthenticated):
        validate_release_access(request, workspace)


def test_validate_upload_access_no_permission(rf):
    backend = BackendFactory()
    user = UserFactory()
    workspace = WorkspaceFactory()

    BackendMembershipFactory(backend=backend, user=user)

    request = rf.get(
        "/",
        headers={
            "authorization": backend.auth_token,
            "os-user": user.username,
        },
    )

    with pytest.raises(NotAuthenticated):
        validate_upload_access(request, workspace)


def test_validate_upload_access_not_a_backend_member(rf, role_factory):
    backend = BackendFactory()
    user = UserFactory(roles=[role_factory(permission=permissions.release_file_upload)])
    workspace = WorkspaceFactory()

    request = rf.get(
        "/",
        headers={
            "authorization": backend.auth_token,
            "os-user": user.username,
        },
    )

    with pytest.raises(NotAuthenticated):
        validate_upload_access(request, workspace)


def test_validate_upload_access_unknown_user(rf):
    backend = BackendFactory()
    workspace = WorkspaceFactory()

    BackendMembershipFactory(backend=backend)

    request = rf.get(
        "/",
        headers={"authorization": backend.auth_token, "os-user": "test"},
    )

    with pytest.raises(NotAuthenticated):
        validate_upload_access(request, workspace)


def test_workspacestatusapi_success(api_rf):
    request = api_rf.get("/")

    project1 = ProjectFactory()
    workspace1 = WorkspaceFactory(project=project1, uses_new_release_flow=True)

    response = WorkspaceStatusAPI.as_view()(request, workspace_id=workspace1.name)
    assert response.status_code == 200
    assert response.data["uses_new_release_flow"]

    project2 = ProjectFactory()
    workspace2 = WorkspaceFactory(project=project2, uses_new_release_flow=False)
    response = WorkspaceStatusAPI.as_view()(request, workspace_id=workspace2.name)
    assert response.status_code == 200
    assert not response.data["uses_new_release_flow"]


def test_level4tokenauthenticationapi_success(
    api_rf, project_membership, token_login_user, role_factory
):
    # give user correct permissions on this project
    project1 = ProjectFactory()
    workspace1 = WorkspaceFactory(project=project1)
    workspace2 = WorkspaceFactory(project=project1)
    project_membership(
        user=token_login_user,
        project=project1,
        roles=[role_factory(permission=permissions.unreleased_outputs_view)],
    )

    # another project, where user does *not* have permissions
    project2 = ProjectFactory()
    WorkspaceFactory(project=project2)
    project_membership(user=token_login_user, project=project2)

    token = generate_login_token(token_login_user)
    backend = token_login_user.backends.first()
    token_data = {"user": token_login_user.username, "token": token}
    request = api_rf.post(
        "/",
        data=token_data,
        headers={"authorization": backend.auth_token},
        format="json",
    )

    response = Level4TokenAuthenticationAPI.as_view()(request)
    assert response.status_code == 200
    assert response.data == {
        "username": token_login_user.username,
        "fullname": token_login_user.fullname,
        "workspaces": {
            workspace1.name: {"project": project1.name},
            workspace2.name: {"project": project1.name},
        },  # should not include workspace3
        "output_checker": False,
        "staff": False,
    }


def test_level4tokenauthenticationapi_success_privileged(
    api_rf, project_membership, token_login_user, role_factory
):
    # enable privileges for user
    token_login_user.roles.append(OutputChecker)
    token_login_user.roles.append(CoreDeveloper)
    token_login_user.is_staff = True
    token_login_user.save()

    project = ProjectFactory()
    project_membership(
        user=token_login_user,
        project=project,
        roles=[role_factory(permission=permissions.unreleased_outputs_view)],
    )
    workspace1 = WorkspaceFactory(project=project)
    workspace2 = WorkspaceFactory(project=project)

    token = generate_login_token(token_login_user)
    backend = token_login_user.backends.first()
    token_data = {"user": token_login_user.username, "token": token}
    request = api_rf.post(
        "/",
        data=token_data,
        headers={"authorization": backend.auth_token},
        format="json",
    )

    response = Level4TokenAuthenticationAPI.as_view()(request)
    assert response.status_code == 200
    assert response.data == {
        "username": token_login_user.username,
        "fullname": token_login_user.fullname,
        "workspaces": {
            workspace1.name: {"project": project.name},
            workspace2.name: {"project": project.name},
        },  # should not include workspace3
        "output_checker": True,
        "staff": True,
    }


def test_level4tokenauthenticationapi_fails_not_backend(
    api_rf, project_membership, token_login_user, role_factory
):
    project = ProjectFactory()
    project_membership(
        user=token_login_user,
        project=project,
        roles=[role_factory(permission=permissions.unreleased_outputs_view)],
    )

    token = generate_login_token(token_login_user)

    token_data = {"user": token_login_user.username, "token": token}
    # do not set authorization header
    request = api_rf.post("/", data=token_data, format="json")

    response = Level4TokenAuthenticationAPI.as_view()(request)
    assert response.status_code == 403
    response_json = json.loads(response.rendered_content)
    assert response_json["detail"] == "Authorization header is missing"


def test_level4tokenauthenticationapi_fails_invalid_token(
    api_rf, project_membership, token_login_user, role_factory
):
    project = ProjectFactory()
    project_membership(
        user=token_login_user,
        project=project,
        roles=[role_factory(permission=permissions.unreleased_outputs_view)],
    )

    generate_login_token(token_login_user)
    backend = token_login_user.backends.first()
    token_data = {"user": token_login_user.username, "token": "bad token"}
    # do not set authorization header
    request = api_rf.post(
        "/",
        data=token_data,
        headers={"authorization": backend.auth_token},
        format="json",
    )

    response = Level4TokenAuthenticationAPI.as_view()(request)
    assert response.status_code == 403
    response_json = json.loads(response.rendered_content)
    assert (
        response_json["detail"] == f"Token for {token_login_user.username} was invalid"
    )


def invalid_users():
    def nonsocial_user():
        user = UserFactory()
        return user, f"User {user.username} is not a github user"

    def social_user():
        # github user but no backends
        social_user = UserFactory()
        UserSocialAuthFactory(user=social_user)
        return (
            social_user,
            f"User {social_user.username} does not have access to any backends",
        )

    yield nonsocial_user
    yield social_user


@pytest.mark.parametrize("user_function", invalid_users())
def test_level4tokenauthenticationapi_fails_invalid_user(
    api_rf, project_membership, user_function, role_factory
):
    user, expected_msg = user_function()
    project = ProjectFactory()
    project_membership(
        user=user,
        project=project,
        roles=[role_factory(permission=permissions.unreleased_outputs_view)],
    )

    backend = BackendFactory()
    token_data = {"user": user.username, "token": "doesn't matter"}
    request = api_rf.post(
        "/",
        data=token_data,
        headers={"authorization": backend.auth_token},
        format="json",
    )

    response = Level4TokenAuthenticationAPI.as_view()(request)
    assert response.status_code == 403
    response_json = json.loads(response.rendered_content)
    assert response_json["detail"] == expected_msg


def test_level4authorisationapi_success(
    api_rf, project_membership, token_login_user, role_factory
):
    # give user correct permissions on this project
    project1 = ProjectFactory()
    workspace1 = WorkspaceFactory(project=project1)
    workspace2 = WorkspaceFactory(project=project1)
    project_membership(
        user=token_login_user,
        project=project1,
        roles=[role_factory(permission=permissions.unreleased_outputs_view)],
    )

    # another project, where user does *not* have permissions
    project2 = ProjectFactory()
    WorkspaceFactory(project=project2)
    project_membership(user=token_login_user, project=project2)

    backend = token_login_user.backends.first()
    request_data = {"user": token_login_user.username}
    request = api_rf.post(
        "/",
        data=request_data,
        headers={"authorization": backend.auth_token},
        format="json",
    )

    response = Level4AuthorisationAPI.as_view()(request)
    assert response.status_code == 200
    assert response.data == {
        "username": token_login_user.username,
        "fullname": token_login_user.fullname,
        "workspaces": {
            workspace1.name: {"project": project1.name},
            workspace2.name: {"project": project1.name},
        },  # should not include workspace3
        "output_checker": False,
        "staff": False,
    }


def test_level4authorisationapi_bad_backend_token(api_rf, token_login_user):
    request_data = {"user": token_login_user.username}
    request = api_rf.post(
        "/",
        data=request_data,
        headers={"authorization": "bad token"},
        format="json",
    )

    response = Level4AuthorisationAPI.as_view()(request)
    assert response.status_code == 403


def test_level4authorisationapi_user_not_exists(api_rf):
    backend = BackendFactory()
    request_data = {"user": "baduser"}
    request = api_rf.post(
        "/",
        data=request_data,
        headers={"authorization": backend.auth_token},
        format="json",
    )

    response = Level4AuthorisationAPI.as_view()(request)
    assert response.status_code == 404


def test_level4authorisationapi_invalid_user(api_rf, user):
    backend = BackendFactory()
    request_data = {"user": user.username}
    request = api_rf.post(
        "/",
        data=request_data,
        headers={"authorization": backend.auth_token},
        format="json",
    )

    response = Level4AuthorisationAPI.as_view()(request)
    assert response.status_code == 403
