import hashlib
import json
import random
import string
from pathlib import Path

import pytest
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from jobserver.api.releases import (
    ReleaseAPI,
    ReleaseFileAPI,
    ReleaseNotificationAPICreate,
    ReleaseWorkspaceAPI,
    ReviewAPI,
    SnapshotAPI,
    SnapshotCreateAPI,
    SnapshotPublishAPI,
    WorkspaceStatusAPI,
    validate_release_access,
    validate_upload_access,
)
from jobserver.authorization import (
    OutputChecker,
    OutputPublisher,
    ProjectCollaborator,
    ProjectDeveloper,
)
from jobserver.models import Release, ReleaseFileReview
from jobserver.utils import set_from_qs
from tests.factories import (
    BackendFactory,
    BackendMembershipFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    ReleaseFactory,
    ReleaseUploadsFactory,
    SnapshotFactory,
    UserFactory,
    WorkspaceFactory,
)
from tests.factories import releases as new_style


def test_releaseapi_get_unknown_release(api_rf):
    request = api_rf.get("/")

    response = ReleaseAPI.as_view()(request, release_id="")

    assert response.status_code == 404


def test_releaseapi_get_with_anonymous_user(api_rf):
    release = ReleaseFactory(ReleaseUploadsFactory(["file.txt"]))

    request = api_rf.get("/")

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 403


def test_releaseapi_get_with_permission(api_rf):
    release = ReleaseFactory(ReleaseUploadsFactory(["file.txt"]))
    rfile = release.files.first()

    ProjectMembershipFactory(
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
                "size": 8,
                "sha256": rfile.filehash,
                "is_deleted": False,
                "backend": release.backend.name,
            }
        ],
    }


def test_releaseapi_get_without_permission(api_rf):
    release = ReleaseFactory(ReleaseUploadsFactory(["file.txt"]))

    request = api_rf.get("/")
    request.user = UserFactory()

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 403


def test_releaseapi_post_already_uploaded(api_rf, tmp_path):
    user = UserFactory(roles=[OutputChecker])

    release = new_style.ReleaseFactory(requested_files=[{"name": "file.txt"}])
    # mirror path building until we can abstract this into a fixture
    path = tmp_path / "releases" / release.workspace.name / "releases" / str(release.id)
    path.mkdir(parents=True)

    rfile = new_style.ReleaseFileFactory(
        release=release,
        name="file.txt",
        path=Path(release.workspace.name) / "releases" / str(release.id) / "file.txt",
        uploaded_at=timezone.now(),
    )
    content = "".join(random.choice(string.ascii_letters) for i in range(10))
    content = content.encode("utf8")
    rfile.absolute_path().write_bytes(content)

    BackendMembershipFactory(backend=release.backend, user=user)

    count_before = release.files.count()

    request = api_rf.post(
        "/",
        content_type="application/octet-stream",
        data=content,
        HTTP_CONTENT_DISPOSITION="attachment; filename=file.txt",
        HTTP_AUTHORIZATION=release.backend.auth_token,
        HTTP_OS_USER=user.username,
    )

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 400
    assert "file.txt" in response.data["detail"]
    assert "already been uploaded" in response.data["detail"]
    assert release.files.count() == count_before


def test_releaseapi_post_bad_backend(api_rf):
    user = UserFactory(roles=[OutputChecker])
    release = new_style.ReleaseFactory(requested_files=[{"name": "file.txt"}])

    bad_backend = BackendFactory()
    BackendMembershipFactory(backend=bad_backend, user=user)

    content = "".join(random.choice(string.ascii_letters) for i in range(10))
    content = content.encode("utf8")
    request = api_rf.post(
        "/",
        content_type="application/octet-stream",
        data=content,
        HTTP_CONTENT_DISPOSITION="attachment; filename=file.txt",
        HTTP_AUTHORIZATION=bad_backend.auth_token,
        HTTP_OS_USER=user.username,
    )

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 400
    assert bad_backend.slug in response.data["detail"]


def test_releaseapi_post_bad_backend_token(api_rf):
    uploads = ReleaseUploadsFactory(["file.txt"])
    release = ReleaseFactory(uploads, uploaded=False)

    request = api_rf.post("/", HTTP_AUTHORIZATION="invalid")

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 403


def test_releaseapi_post_bad_filename(api_rf):
    user = UserFactory(roles=[OutputChecker])
    release = new_style.ReleaseFactory()

    BackendMembershipFactory(backend=release.backend, user=user)

    content = "".join(random.choice(string.ascii_letters) for i in range(10))
    content = content.encode("utf8")
    request = api_rf.post(
        "/",
        content_type="application/octet-stream",
        data=content,
        HTTP_CONTENT_DISPOSITION="attachment; filename=wrongname.txt",
        HTTP_AUTHORIZATION=release.backend.auth_token,
        HTTP_OS_USER=user.username,
    )

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 400
    assert "wrongname.txt" in response.data["detail"]


def test_releaseapi_post_bad_user(api_rf):
    uploads = ReleaseUploadsFactory(["file.txt"])
    release = ReleaseFactory(uploads, uploaded=False)

    request = api_rf.post(
        "/",
        HTTP_AUTHORIZATION=release.backend.auth_token,
        HTTP_OS_USER="baduser",
    )

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 403


def test_releaseapi_post_no_files(api_rf):
    user = UserFactory(roles=[OutputChecker])
    uploads = ReleaseUploadsFactory(["file.txt"])
    release = ReleaseFactory(uploads, uploaded=False)

    BackendMembershipFactory(backend=release.backend, user=user)

    request = api_rf.post(
        "/",
        HTTP_CONTENT_DISPOSITION=f"attachment; filename={uploads[0].filename}",
        HTTP_AUTHORIZATION=release.backend.auth_token,
        HTTP_OS_USER=user.username,
    )

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 400
    assert "No data" in response.data["detail"]


def test_releaseapi_post_no_user(api_rf):
    uploads = ReleaseUploadsFactory(["file.txt"])
    release = ReleaseFactory(uploads, uploaded=False)

    request = api_rf.post(
        "/",
        HTTP_AUTHORIZATION=release.backend.auth_token,
    )

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 403


def test_releaseapi_post_success(api_rf, slack_messages):
    creating_user = UserFactory()
    uploading_user = UserFactory(roles=[OutputChecker])

    backend = BackendFactory(name="test-backend")
    release = new_style.ReleaseFactory(
        backend=backend,
        created_by=creating_user,
        requested_files=[{"name": "file.txt"}],
    )
    content = "".join(random.choice(string.ascii_letters) for i in range(10))
    content = content.encode("utf8")
    filehash = hashlib.sha256(content).hexdigest()
    rfile = new_style.ReleaseFileFactory(
        release=release,
        created_by=uploading_user,
        name="file.txt",
        path="test/file.txt",
        filehash=filehash,
    )

    BackendMembershipFactory(backend=release.backend, user=creating_user)
    BackendMembershipFactory(backend=release.backend, user=uploading_user)

    request = api_rf.post(
        "/",
        content_type="application/octet-stream",
        data=content,
        HTTP_CONTENT_DISPOSITION="attachment; filename=file.txt",
        HTTP_AUTHORIZATION=release.backend.auth_token,
        HTTP_OS_USER=uploading_user.username,
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


def test_releaseapi_post_unknown_release(api_rf):
    request = api_rf.post("/")

    response = ReleaseAPI.as_view()(request, release_id="")

    assert response.status_code == 404


def test_releaseapi_post_with_no_backend_token(api_rf):
    uploads = ReleaseUploadsFactory(["file.txt"])
    release = ReleaseFactory(uploads, uploaded=False)

    request = api_rf.post("/")

    response = ReleaseAPI.as_view()(request, release_id=release.id)

    assert response.status_code == 403


def test_releasenotificationapicreate_success(api_rf, slack_messages):
    backend = BackendFactory(name="test")

    data = {
        "created_by": "test user",
        "path": "/path/to/outputs",
    }
    request = api_rf.post("/", data, HTTP_AUTHORIZATION=backend.auth_token)
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
    request = api_rf.post("/", data, HTTP_AUTHORIZATION=backend.auth_token)
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

    response = ReleaseWorkspaceAPI.as_view()(request, workspace_name="")

    assert response.status_code == 404


def test_releaseworkspaceapi_get_with_anonymous_user(api_rf):
    workspace = WorkspaceFactory()

    request = api_rf.get("/")

    response = ReleaseWorkspaceAPI.as_view()(request, workspace_name=workspace.name)

    assert response.status_code == 403


def test_releaseworkspaceapi_get_with_permission(api_rf):
    workspace = WorkspaceFactory()
    backend1 = BackendFactory(slug="backend1")
    backend2 = BackendFactory(slug="backend2")
    user = UserFactory()
    ProjectMembershipFactory(
        user=user, project=workspace.project, roles=[ProjectCollaborator]
    )

    # two release for same filename but different content
    release1 = ReleaseFactory(
        ReleaseUploadsFactory({"file1.txt": b"backend1"}),
        workspace=workspace,
        backend=backend1,
        created_by=user,
    )
    release2 = ReleaseFactory(
        ReleaseUploadsFactory({"file1.txt": b"backend2"}),
        workspace=workspace,
        backend=backend2,
        created_by=user,
    )

    request = api_rf.get("/")
    request.user = user

    response = ReleaseWorkspaceAPI.as_view()(request, workspace_name=workspace.name)

    assert response.status_code == 200
    assert response.data == {
        "files": [
            {
                "name": "backend2/file1.txt",
                "id": release2.files.first().pk,
                "url": f"/api/v2/releases/file/{release2.files.first().id}",
                "user": user.username,
                "date": release2.files.first().created_at.isoformat(),
                "size": 8,
                "sha256": release2.files.first().filehash,
                "is_deleted": False,
                "backend": release2.backend.name,
            },
            {
                "name": "backend1/file1.txt",
                "id": release1.files.first().pk,
                "url": f"/api/v2/releases/file/{release1.files.first().id}",
                "user": user.username,
                "date": release1.files.first().created_at.isoformat(),
                "size": 8,
                "sha256": release1.files.first().filehash,
                "is_deleted": False,
                "backend": release1.backend.name,
            },
        ],
    }


def test_releaseworkspaceapi_get_without_permission(api_rf):
    workspace = WorkspaceFactory()

    request = api_rf.get("/")
    request.user = UserFactory()

    response = ReleaseWorkspaceAPI.as_view()(request, workspace_name=workspace.name)

    assert response.status_code == 403


def test_releaseworkspaceapi_post_create_release(api_rf, slack_messages):
    user = UserFactory(roles=[OutputChecker])
    workspace = WorkspaceFactory()
    ProjectMembershipFactory(user=user, project=workspace.project)

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
        HTTP_AUTHORIZATION="test",
        HTTP_OS_USER=user.username,
    )

    response = ReleaseWorkspaceAPI.as_view()(request, workspace_name=workspace.name)

    assert response.status_code == 201, response.data
    assert Release.objects.count() == 1

    release = Release.objects.first()
    assert response["Release-Id"] == str(release.id)
    assert response["Location"] == f"http://testserver{release.get_api_url()}"

    assert len(slack_messages) == 1
    text, channel = slack_messages[0]

    assert channel == "opensafely-releases"
    assert f"{user.get_staff_url()}|{user.name}>" in text
    assert f"{release.get_absolute_url()}|release>" in text
    assert f"{workspace.get_absolute_url()}|{workspace.name}>" in text
    assert backend.name in text


def test_releaseworkspaceapi_post_release_already_exists(api_rf):
    user = UserFactory(roles=[OutputChecker])

    release = new_style.ReleaseFactory()
    rfile = new_style.ReleaseFileFactory(
        release=release,
        created_by=user,
        name="file.txt",
        filehash="hash",
    )

    BackendMembershipFactory(backend=release.backend, user=user)
    ProjectMembershipFactory(project=release.workspace.project, user=user)

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
        HTTP_AUTHORIZATION=release.backend.auth_token,
        HTTP_OS_USER=user.username,
    )

    response = ReleaseWorkspaceAPI.as_view()(
        request, workspace_name=release.workspace.name
    )

    assert response.status_code == 400
    assert "file.txt" in response.data["detail"]
    assert "already been uploaded" in response.data["detail"]


def test_releaseworkspaceapi_post_unknown_workspace(api_rf):
    request = api_rf.post("/")

    response = ReleaseWorkspaceAPI.as_view()(request, workspace_name="")

    assert response.status_code == 404


def test_releaseworkspaceapi_post_with_bad_backend_token(api_rf):
    workspace = WorkspaceFactory()
    BackendFactory(auth_token="test")

    request = api_rf.post("/", HTTP_AUTHORIZATION="invalid")

    response = ReleaseWorkspaceAPI.as_view()(request, workspace_name=workspace.name)

    assert response.status_code == 403


def test_releaseworkspaceapi_post_with_bad_json(api_rf):
    user = UserFactory(roles=[OutputChecker])
    workspace = WorkspaceFactory()
    ProjectMembershipFactory(user=user, project=workspace.project)

    backend = BackendFactory(auth_token="test")
    BackendMembershipFactory(backend=backend, user=user)

    request = api_rf.post(
        "/",
        content_type="application/json",
        data=json.dumps({}),
        HTTP_CONTENT_DISPOSITION="attachment; filename=release.zip",
        HTTP_AUTHORIZATION="test",
        HTTP_OS_USER=user.username,
    )

    response = ReleaseWorkspaceAPI.as_view()(request, workspace_name=workspace.name)

    assert response.status_code == 400


def test_releaseworkspaceapi_post_with_bad_user(api_rf):
    workspace = WorkspaceFactory()
    BackendFactory(auth_token="test")

    request = api_rf.post(
        "/",
        HTTP_AUTHORIZATION="test",
        HTTP_OS_USER="baduser",
    )

    response = ReleaseWorkspaceAPI.as_view()(request, workspace_name=workspace.name)

    assert response.status_code == 403


def test_releaseworkspaceapi_post_without_backend_token(api_rf):
    workspace = WorkspaceFactory()

    request = api_rf.post("/")

    response = ReleaseWorkspaceAPI.as_view()(request, workspace_name=workspace.name)

    assert response.status_code == 403


def test_releaseworkspaceapi_post_without_user(api_rf):
    workspace = WorkspaceFactory()
    BackendFactory(auth_token="test")

    request = api_rf.post(
        "/",
        HTTP_AUTHORIZATION="test",
    )

    response = ReleaseWorkspaceAPI.as_view()(request, workspace_name=workspace.name)

    assert response.status_code == 403


def test_releasefileapi_get_unknown_file(api_rf):
    request = api_rf.get("/")

    response = ReleaseFileAPI.as_view()(request, file_id="")

    assert response.status_code == 404


def test_releasefileapi_with_anonymous_user(api_rf):
    release = ReleaseFactory(ReleaseUploadsFactory(["file1.txt"]))
    rfile = release.files.first()

    request = api_rf.get("/")

    response = ReleaseFileAPI.as_view()(request, file_id=rfile.id)

    assert response.status_code == 403


def test_releasefileapi_with_deleted_file(api_rf):
    uploads = ReleaseUploadsFactory({"file.txt": b"test"})
    release = ReleaseFactory(uploads)
    rfile = release.files.first()
    user = UserFactory()

    ProjectMembershipFactory(
        user=user,
        project=release.workspace.project,
        roles=[ProjectCollaborator],
    )

    # delete file
    rfile.absolute_path().unlink()

    request = api_rf.get("/")
    request.user = user

    response = ReleaseFileAPI.as_view()(request, file_id=rfile.id)

    assert response.status_code == 404


def test_releasefileapi_with_nginx_redirect(api_rf):
    uploads = ReleaseUploadsFactory({"file.txt": b"test"})
    release = ReleaseFactory(uploads)
    rfile = release.files.first()
    user = UserFactory()

    # test nginx configuration
    ProjectMembershipFactory(
        user=user,
        project=release.workspace.project,
        roles=[ProjectCollaborator],
    )

    request = api_rf.get("/", HTTP_RELEASES_REDIRECT="/storage")
    request.user = user

    response = ReleaseFileAPI.as_view()(request, file_id=rfile.id)

    assert response.status_code == 200
    assert (
        response.headers["X-Accel-Redirect"]
        == f"/storage/{release.workspace.name}/releases/{release.id}/file.txt"
    )


def test_releasefileapi_with_permission(api_rf):
    uploads = ReleaseUploadsFactory({"file.txt": b"test"})
    release = ReleaseFactory(uploads)
    rfile = release.files.first()
    user = UserFactory()

    # logged in, with permission
    ProjectMembershipFactory(
        user=user,
        project=release.workspace.project,
        roles=[ProjectCollaborator],
    )

    request = api_rf.get("/")
    request.user = user

    response = ReleaseFileAPI.as_view()(request, file_id=rfile.id)

    assert response.status_code == 200
    assert b"".join(response.streaming_content) == b"test"
    assert response.headers["Content-Type"] == "text/plain"


def test_releasefileapi_without_permission(api_rf):
    release = ReleaseFactory(ReleaseUploadsFactory(["file1.txt"]))
    rfile = release.files.first()

    request = api_rf.get("/")
    request.user = UserFactory()  # logged in, but no permission

    response = ReleaseFileAPI.as_view()(request, file_id=rfile.id)

    assert response.status_code == 403


def test_reviewapi_without_permission(api_rf):
    release = new_style.ReleaseFactory()

    data = {
        "files": [],
        "metadata": {},
        "review": {},
    }
    request = api_rf.post("/", data=data, format="json")

    response = ReviewAPI.as_view()(request, release_id=release.pk)

    assert response.status_code == 200, response.data


def test_reviewapi_unknown_filename_or_content(api_rf):
    release = new_style.ReleaseFactory()
    new_style.ReleaseFileFactory(release=release, name="test1", filehash="test1")
    new_style.ReleaseFileFactory(release=release, name="test2", filehash="test2")

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
    release = new_style.ReleaseFactory()
    new_style.ReleaseFileFactory(release=release, name="test1", filehash="test1")
    new_style.ReleaseFileFactory(release=release, name="test2", filehash="test2")

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


def test_snapshotapi_published_with_anonymous_user(api_rf, freezer):
    snapshot = SnapshotFactory(published_at=timezone.now())

    request = api_rf.get("/")

    response = SnapshotAPI.as_view()(
        request,
        workspace_id=snapshot.workspace.name,
        snapshot_id=snapshot.pk,
    )

    assert response.status_code == 200
    assert response.data == {"files": []}


def test_snapshotapi_published_with_permission(api_rf):
    snapshot = SnapshotFactory(published_at=timezone.now())
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
    snapshot = SnapshotFactory(published_at=timezone.now())

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
    snapshot = SnapshotFactory(published_at=None)

    request = api_rf.get("/")

    response = SnapshotAPI.as_view()(
        request,
        workspace_id=snapshot.workspace.name,
        snapshot_id=snapshot.pk,
    )

    assert response.status_code == 403


def test_snapshotapi_unpublished_with_permission(api_rf):
    snapshot = SnapshotFactory(published_at=None)

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
    snapshot = SnapshotFactory(published_at=None)

    request = api_rf.get("/")
    request.user = UserFactory()  # logged in, but no permission

    response = SnapshotAPI.as_view()(
        request,
        workspace_id=snapshot.workspace.name,
        snapshot_id=snapshot.pk,
    )

    assert response.status_code == 403


def test_snapshotcreate_unknown_files(api_rf):
    workspace = WorkspaceFactory()
    user = UserFactory()
    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = api_rf.post("/", data={"file_ids": ["test"]})
    request.user = user

    response = SnapshotCreateAPI.as_view()(request, workspace_id=workspace.name)

    assert response.status_code == 400, response.data
    assert "Unknown file IDs" in response.data["detail"], response.data


def test_snapshotcreate_with_existing_snapshot(api_rf):
    workspace = WorkspaceFactory()
    uploads = ReleaseUploadsFactory({"file1.txt": b"test1"})
    release = ReleaseFactory(uploads, workspace=workspace)
    snapshot = SnapshotFactory(workspace=workspace)
    snapshot.files.set(release.files.all())

    user = UserFactory()
    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    request = api_rf.post("/", data={"file_ids": [release.files.first().pk]})
    request.user = user

    response = SnapshotCreateAPI.as_view()(request, workspace_id=workspace.name)

    assert response.status_code == 400, response.data

    msg = "A release with the current files already exists"
    assert msg in response.data["detail"], response.data


def test_snapshotcreate_with_permission(api_rf):
    workspace = WorkspaceFactory()
    uploads = ReleaseUploadsFactory(
        {
            "file1.txt": b"test1",
            "file2.txt": b"test2",
            "file3.txt": b"test3",
            "file4.txt": b"test4",
            "file5.txt": b"test5",
        }
    )
    release = ReleaseFactory(uploads, workspace=workspace)

    user = UserFactory()
    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
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


def test_snapshotpublishapi_already_published(api_rf):
    snapshot = SnapshotFactory(published_at=timezone.now())

    assert snapshot.is_published

    request = api_rf.post("/")
    request.user = UserFactory(roles=[OutputPublisher])

    response = SnapshotPublishAPI.as_view()(
        request,
        workspace_id=snapshot.workspace.name,
        snapshot_id=snapshot.pk,
    )

    assert response.status_code == 200

    snapshot.refresh_from_db()
    assert snapshot.is_published


def test_snapshotpublishapi_success(api_rf):
    snapshot = SnapshotFactory()

    assert snapshot.is_draft

    request = api_rf.post("/")
    request.user = UserFactory(roles=[OutputPublisher])

    response = SnapshotPublishAPI.as_view()(
        request,
        workspace_id=snapshot.workspace.name,
        snapshot_id=snapshot.pk,
    )

    assert response.status_code == 200

    snapshot.refresh_from_db()
    assert snapshot.is_published


def test_snapshotpublishapi_unknown_snapshot(api_rf):
    workspace = WorkspaceFactory()

    request = api_rf.post("/")
    request.user = UserFactory(roles=[OutputPublisher])

    response = SnapshotPublishAPI.as_view()(
        request,
        workspace_id=workspace.name,
        snapshot_id=0,
    )

    assert response.status_code == 404


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

    request = rf.get("/", HTTP_AUTHORIZATION=f"{user.username}:{token}")
    request.user = AnonymousUser()

    assert validate_release_access(request, workspace) is None


def test_validate_release_access_with_auth_header_and_invalid_token(rf):
    user = UserFactory()
    workspace = WorkspaceFactory()

    # set a token so the user is considered a bot
    user.rotate_token()

    request = rf.get("/", HTTP_AUTHORIZATION=f"{user.username}:invalid")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        validate_release_access(request, workspace)


def test_validate_release_access_with_auth_header_and_unknown_user(rf):
    user = UserFactory()
    workspace = WorkspaceFactory()

    token = user.rotate_token()

    request = rf.get("/", HTTP_AUTHORIZATION=f"0:{token}")
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
        HTTP_AUTHORIZATION=backend.auth_token,
        HTTP_OS_USER=user.username,
    )

    with pytest.raises(NotAuthenticated):
        validate_upload_access(request, workspace)


def test_validate_upload_access_not_a_backend_member(rf):
    backend = BackendFactory()
    user = UserFactory(roles=[OutputChecker])
    workspace = WorkspaceFactory()

    request = rf.get(
        "/",
        HTTP_AUTHORIZATION=backend.auth_token,
        HTTP_OS_USER=user.username,
    )

    with pytest.raises(NotAuthenticated):
        validate_upload_access(request, workspace)


def test_validate_upload_access_unknown_user(rf):
    backend = BackendFactory()
    workspace = WorkspaceFactory()

    BackendMembershipFactory(backend=backend)

    request = rf.get("/", HTTP_AUTHORIZATION=backend.auth_token, HTTP_OS_USER="test")

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
