import json

import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from slack_sdk.errors import SlackApiError

from jobserver.api.releases import ReleaseNotificationAPICreate
from jobserver.authorization import ProjectCollaborator, ProjectDeveloper
from jobserver.models import Release
from jobserver.utils import set_from_qs
from tests.factories import (
    BackendFactory,
    ProjectMembershipFactory,
    ReleaseFactory,
    ReleaseUploadsFactory,
    SnapshotFactory,
    UserFactory,
    WorkspaceFactory,
)


@pytest.mark.django_db
def test_releasenotificationapicreate_success(api_rf, mocker):
    backend = BackendFactory()

    mock = mocker.patch("jobserver.api.releases.slack_client", autospec=True)

    data = {
        "created_by": "test user",
        "path": "/path/to/outputs",
    }
    request = api_rf.post("/", data, HTTP_AUTHORIZATION=backend.auth_token)
    request.user = UserFactory()

    response = ReleaseNotificationAPICreate.as_view()(request)

    assert response.status_code == 201, response.data

    # check we called the slack API in the expected way
    mock.chat_postMessage.assert_called_once_with(
        channel="opensafely-outputs",
        text="test user released outputs from /path/to/outputs",
    )


@pytest.mark.django_db
def test_releasenotificationapicreate_success_with_files(api_rf, mocker):
    backend = BackendFactory()

    mock = mocker.patch("jobserver.api.releases.slack_client", autospec=True)

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
    mock.chat_postMessage.assert_called_once_with(
        channel="opensafely-outputs",
        text=(
            "test user released 2 outputs from /path/to/outputs:\n"
            "`output/file1.txt`\n"
            "`output/file2.txt`"
        ),
    )


@pytest.mark.django_db
def test_releasenotificationapicreate_with_failed_slack_update(
    api_rf, mocker, log_output
):
    backend = BackendFactory()

    assert len(log_output.entries) == 0, log_output.entries

    # have the slack API client raise an exception
    mock = mocker.patch("jobserver.api.releases.slack_client", autospec=True)
    mock.chat_postMessage.side_effect = SlackApiError(
        message="an error", response={"error": "an error occurred"}
    )

    data = {
        "created_by": "test user",
        "path": "/path/to/outputs",
    }
    request = api_rf.post("/", data, HTTP_AUTHORIZATION=backend.auth_token)
    request.user = UserFactory()

    response = ReleaseNotificationAPICreate.as_view()(request)

    assert response.status_code == 201, response.data

    # check we called the slack API in the expected way
    mock.chat_postMessage.assert_called_once_with(
        channel="opensafely-outputs",
        text="test user released outputs from /path/to/outputs",
    )

    # check we logged the slack failure
    assert len(log_output.entries) == 1, log_output.entries
    assert log_output.entries[0] == {
        "exc_info": True,
        "event": "Failed to notify slack",
        "log_level": "error",
    }


@pytest.mark.django_db
def test_workspace_api_create_release_no_workspace():
    response = APIClient().post("/api/v2/releases/workspace/notexists")
    assert response.status_code == 404


@pytest.mark.django_db
def test_workspace_api_create_release_no_backend_token():
    workspace = WorkspaceFactory()
    response = APIClient().post(f"/api/v2/releases/workspace/{workspace.name}")
    assert response.status_code == 403


@pytest.mark.django_db
def test_workspace_api_create_release_bad_backend_token():
    workspace = WorkspaceFactory()
    BackendFactory(auth_token="test")

    response = APIClient().post(
        f"/api/v2/releases/workspace/{workspace.name}",
        HTTP_AUTHORIZATION="invalid",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_workspace_api_create_release_no_user():
    workspace = WorkspaceFactory()
    BackendFactory(auth_token="test")
    response = APIClient().post(
        f"/api/v2/releases/workspace/{workspace.name}",
        HTTP_AUTHORIZATION="test",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_workspace_api_create_release_bad_user():
    workspace = WorkspaceFactory()
    BackendFactory(auth_token="test")
    response = APIClient().post(
        f"/api/v2/releases/workspace/{workspace.name}",
        HTTP_AUTHORIZATION="test",
        HTTP_OS_USER="baduser",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_workspace_api_create_release_created():
    user = UserFactory()
    workspace = WorkspaceFactory()
    ProjectMembershipFactory(user=user, project=workspace.project)
    BackendFactory(auth_token="test")

    assert Release.objects.count() == 0

    response = APIClient().post(
        f"/api/v2/releases/workspace/{workspace.name}",
        content_type="application/json",
        data=json.dumps({"files": {"file1.txt": "hash"}}),
        HTTP_AUTHORIZATION="test",
        HTTP_OS_USER=user.username,
    )

    assert response.status_code == 201
    assert Release.objects.count() == 1

    release = Release.objects.first()
    assert response["Release-Id"] == str(release.id)
    assert response["Location"] == f"http://testserver{release.get_api_url()}"


@pytest.mark.django_db
def test_workspace_api_create_release_already_exists():
    release = ReleaseFactory(ReleaseUploadsFactory(["file.txt"]))
    rfile = release.files.first()
    ProjectMembershipFactory(user=release.created_by, project=release.workspace.project)

    response = APIClient().post(
        f"/api/v2/releases/workspace/{release.workspace.name}",
        content_type="application/json",
        data=json.dumps({"files": {"file.txt": rfile.filehash}}),
        HTTP_AUTHORIZATION=release.backend.auth_token,
        HTTP_OS_USER=release.created_by.username,
    )

    assert response.status_code == 400
    assert "file.txt" in response.data["detail"]
    assert "already exists" in response.data["detail"]


@pytest.mark.django_db
def test_workspace_api_create_release_bad_json():
    user = UserFactory()
    workspace = WorkspaceFactory()
    ProjectMembershipFactory(user=user, project=workspace.project)
    BackendFactory(auth_token="test")

    response = APIClient().post(
        f"/api/v2/releases/workspace/{workspace.name}",
        content_type="application/json",
        data=json.dumps({}),
        HTTP_CONTENT_DISPOSITION="attachment; filename=release.zip",
        HTTP_AUTHORIZATION="test",
        HTTP_OS_USER=user.username,
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_workspace_index_api_not_exists():
    client = APIClient()
    response = client.get("/api/v2/releases/workspace/badid")
    assert response.status_code == 404


@pytest.mark.django_db
def test_workspace_index_api_anonymous():
    workspace = WorkspaceFactory()
    client = APIClient()

    index_url = f"/api/v2/releases/workspace/{workspace.name}"
    response = client.get(index_url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_workspace_index_api_logged_in_no_permission():
    workspace = WorkspaceFactory()
    client = APIClient()
    user = UserFactory()

    client.force_authenticate(user=user)
    index_url = f"/api/v2/releases/workspace/{workspace.name}"
    response = client.get(index_url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_workspace_index_api_have_permission():
    workspace = WorkspaceFactory()
    backend1 = BackendFactory(name="backend1")
    backend2 = BackendFactory(name="backend2")
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user=user)
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

    index_url = f"/api/v2/releases/workspace/{workspace.name}"
    response = client.get(index_url)
    assert response.status_code == 200
    assert response.json() == {
        "files": [
            {
                "name": "backend2/file1.txt",
                "id": release2.files.first().pk,
                "url": f"/api/v2/releases/file/{release2.files.first().id}",
                "user": user.username,
                "date": release2.files.first().created_at.isoformat(),
                "size": 8,
                "sha256": release2.files.first().filehash,
            },
            {
                "name": "backend1/file1.txt",
                "id": release1.files.first().pk,
                "url": f"/api/v2/releases/file/{release1.files.first().id}",
                "user": user.username,
                "date": release1.files.first().created_at.isoformat(),
                "size": 8,
                "sha256": release1.files.first().filehash,
            },
        ],
    }


@pytest.mark.django_db
def test_release_index_api_not_exists():
    client = APIClient()
    # bad id
    response = client.get("/api/v2/releases/release/badid")
    assert response.status_code == 404


@pytest.mark.django_db
def test_release_index_api_anonymous():
    release = ReleaseFactory(ReleaseUploadsFactory(["file.txt"]))
    client = APIClient()
    index_url = f"/api/v2/releases/release/{release.id}"

    response = client.get(index_url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_release_index_api_logged_in_no_permission():
    release = ReleaseFactory(ReleaseUploadsFactory(["file.txt"]))
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user=user)

    index_url = f"/api/v2/releases/release/{release.id}"
    response = client.get(index_url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_release_index_api_have_permission():
    release = ReleaseFactory(ReleaseUploadsFactory(["file.txt"]))
    rfile = release.files.first()
    client = APIClient()

    ProjectMembershipFactory(
        user=release.created_by,
        project=release.workspace.project,
        roles=[ProjectCollaborator],
    )
    client.force_authenticate(user=release.created_by)
    index_url = f"/api/v2/releases/release/{release.id}"
    response = client.get(index_url)
    rfile = release.files.first()
    assert response.status_code == 200
    assert response.json() == {
        "files": [
            {
                "name": "file.txt",
                "id": rfile.pk,
                "url": f"/api/v2/releases/file/{rfile.id}",
                "user": rfile.created_by.username,
                "date": rfile.created_at.isoformat(),
                "size": 8,
                "sha256": rfile.filehash,
            }
        ],
    }


@pytest.mark.django_db
def test_release_api_upload_no_release():
    response = APIClient().post("/api/v2/releases/release/notexists")
    assert response.status_code == 404


@pytest.mark.django_db
def test_release_api_upload_no_backend_token():
    uploads = ReleaseUploadsFactory(["file.txt"])
    release = ReleaseFactory(uploads, uploaded=False)
    response = APIClient().post(f"/api/v2/releases/release/{release.id}")
    assert response.status_code == 403


@pytest.mark.django_db
def test_release_api_upload_bad_backend_token():
    uploads = ReleaseUploadsFactory(["file.txt"])
    release = ReleaseFactory(uploads, uploaded=False)
    response = APIClient().post(
        f"/api/v2/releases/release/{release.id}",
        HTTP_AUTHORIZATION="invalid",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_release_api_upload_no_user():
    uploads = ReleaseUploadsFactory(["file.txt"])
    release = ReleaseFactory(uploads, uploaded=False)
    response = APIClient().post(
        f"/api/v2/releases/release/{release.id}",
        HTTP_AUTHORIZATION=release.backend.auth_token,
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_release_api_upload_bad_user():
    uploads = ReleaseUploadsFactory(["file.txt"])
    release = ReleaseFactory(uploads, uploaded=False)
    response = APIClient().post(
        f"/api/v2/releases/release/{release.id}",
        HTTP_AUTHORIZATION=release.backend.auth_token,
        HTTP_OS_USER="baduser",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_release_api_upload_no_files():
    user = UserFactory()
    uploads = ReleaseUploadsFactory(["file.txt"])
    release = ReleaseFactory(uploads, uploaded=False)

    response = APIClient().post(
        f"/api/v2/releases/release/{release.id}",
        HTTP_CONTENT_DISPOSITION=f"attachment; filename={uploads[0].filename}",
        HTTP_AUTHORIZATION=release.backend.auth_token,
        HTTP_OS_USER=user.username,
    )

    assert response.status_code == 400
    assert "No data" in response.data["detail"]


@pytest.mark.django_db
def test_release_api_upload_bad_backend():
    user = UserFactory()
    uploads = ReleaseUploadsFactory(["file.txt"])
    release = ReleaseFactory(uploads, uploaded=False)
    bad_backend = BackendFactory()

    response = APIClient().post(
        f"/api/v2/releases/release/{release.id}",
        content_type="application/octet-stream",
        data=uploads[0].contents,
        HTTP_CONTENT_DISPOSITION=f"attachment; filename={uploads[0].filename}",
        HTTP_AUTHORIZATION=bad_backend.auth_token,
        HTTP_OS_USER=user.username,
    )

    assert response.status_code == 400
    assert bad_backend.name in response.data["detail"]


@pytest.mark.django_db
def test_release_api_upload_bad_filename():
    user = UserFactory()
    uploads = ReleaseUploadsFactory(["file.txt"])
    release = ReleaseFactory(uploads, uploaded=False)

    response = APIClient().post(
        f"/api/v2/releases/release/{release.id}",
        content_type="application/octet-stream",
        data=uploads[0].contents,
        HTTP_CONTENT_DISPOSITION="attachment; filename=wrongname.txt",
        HTTP_AUTHORIZATION=release.backend.auth_token,
        HTTP_OS_USER=user.username,
    )

    assert response.status_code == 400
    assert "wrongname.txt" in response.data["detail"]


@pytest.mark.django_db
def test_release_api_upload_success():
    user = UserFactory()
    uploads = ReleaseUploadsFactory(["file.txt"])
    release = ReleaseFactory(uploads, uploaded=False)

    response = APIClient().post(
        f"/api/v2/releases/release/{release.id}",
        content_type="application/octet-stream",
        data=uploads[0].contents,
        HTTP_CONTENT_DISPOSITION=f"attachment; filename={uploads[0].filename}",
        HTTP_AUTHORIZATION=release.backend.auth_token,
        HTTP_OS_USER=user.username,
    )

    rfile = release.files.first()
    assert response.status_code == 201
    assert response.headers["Location"].endswith(f"/releases/file/{rfile.id}")
    assert response.headers["File-Id"] == rfile.id


@pytest.mark.django_db
def test_release_api_upload_already_uploaded():
    user = UserFactory()
    uploads = ReleaseUploadsFactory(["file.txt"])
    release = ReleaseFactory(uploads, uploaded=True)

    count_before = release.files.count()

    response = APIClient().post(
        f"/api/v2/releases/release/{release.id}",
        content_type="application/octet-stream",
        data=uploads[0].contents,
        HTTP_CONTENT_DISPOSITION=f"attachment; filename={uploads[0].filename}",
        HTTP_AUTHORIZATION=release.backend.auth_token,
        HTTP_OS_USER=user.username,
    )

    assert response.status_code == 400
    assert "file.txt" in response.data["detail"]
    assert "already exists" in response.data["detail"]
    assert release.files.count() == count_before


@pytest.mark.django_db
def test_release_file_api_release_not_exists():
    client = APIClient()

    response = client.get("/api/v2/releases/release/badid/file.txt")
    assert response.status_code == 404


@pytest.mark.django_db
def test_release_file_api_anonymous():
    release = ReleaseFactory(ReleaseUploadsFactory(["file1.txt"]))
    rfile = release.files.first()
    client = APIClient()
    file_url = f"/api/v2/releases/file/{rfile.id}"

    response = client.get(file_url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_release_file_api_no_permission():
    release = ReleaseFactory(ReleaseUploadsFactory(["file1.txt"]))
    rfile = release.files.first()
    user = UserFactory()
    client = APIClient()
    file_url = f"/api/v2/releases/file/{rfile.id}"

    # logged in, but no permission
    client.force_authenticate(user=user)
    response = client.get(file_url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_release_file_api_have_permission():
    uploads = ReleaseUploadsFactory({"file.txt": b"test"})
    release = ReleaseFactory(uploads)
    rfile = release.files.first()
    user = UserFactory()
    client = APIClient()
    file_url = f"/api/v2/releases/file/{rfile.id}"

    # logged in, with permission
    ProjectMembershipFactory(
        user=user,
        project=release.workspace.project,
        roles=[ProjectCollaborator],
    )
    client.force_authenticate(user=user)
    response = client.get(file_url)
    assert response.status_code == 200
    assert b"".join(response.streaming_content) == b"test"
    assert response.headers["Content-Type"] == "text/plain"


@pytest.mark.django_db
def test_release_file_api_nginx_redirect():
    uploads = ReleaseUploadsFactory({"file.txt": b"test"})
    release = ReleaseFactory(uploads)
    rfile = release.files.first()
    user = UserFactory()
    client = APIClient()
    file_url = f"/api/v2/releases/file/{rfile.id}"

    # test nginx configuration
    ProjectMembershipFactory(
        user=user,
        project=release.workspace.project,
        roles=[ProjectCollaborator],
    )
    client.force_authenticate(user=user)
    response = client.get(file_url, HTTP_RELEASES_REDIRECT="/storage")
    assert response.status_code == 200
    assert (
        response.headers["X-Accel-Redirect"]
        == f"/storage/{release.workspace.name}/releases/{release.id}/file.txt"
    )


@pytest.mark.django_db
def test_release_file_api_file_deleted():
    uploads = ReleaseUploadsFactory({"file.txt": b"test"})
    release = ReleaseFactory(uploads)
    rfile = release.files.first()
    user = UserFactory()
    client = APIClient()

    ProjectMembershipFactory(
        user=user,
        project=release.workspace.project,
        roles=[ProjectCollaborator],
    )
    client.force_authenticate(user=user)

    # delete file
    rfile.absolute_path().unlink()
    response = client.get(f"/api/v2/releases/file/{rfile.id}")

    assert response.status_code == 404


@pytest.mark.django_db
def test_snapshot_api_published_anonymous(freezer):
    snapshot = SnapshotFactory(published_at=timezone.now())

    client = APIClient()
    response = client.get(
        f"/api/v2/workspaces/{snapshot.workspace.name}/snapshots/{snapshot.pk}"
    )

    assert response.status_code == 200
    assert response.data == {"files": []}


@pytest.mark.django_db
def test_snapshot_api_published_no_permission():
    snapshot = SnapshotFactory(published_at=timezone.now())

    client = APIClient()
    # logged in, but no permission
    client.force_authenticate(user=UserFactory())

    response = client.get(
        f"/api/v2/workspaces/{snapshot.workspace.name}/snapshots/{snapshot.pk}"
    )

    assert response.status_code == 200
    assert response.data == {"files": []}


@pytest.mark.django_db
def test_snapshot_api_published_with_permission():
    snapshot = SnapshotFactory(published_at=timezone.now())

    client = APIClient()
    client.force_authenticate(user=UserFactory(roles=[ProjectCollaborator]))

    response = client.get(
        f"/api/v2/workspaces/{snapshot.workspace.name}/snapshots/{snapshot.pk}"
    )

    assert response.status_code == 200
    assert response.data == {"files": []}


@pytest.mark.django_db
def test_snapshot_api_unpublished_anonymous():
    snapshot = SnapshotFactory(published_at=None)

    client = APIClient()
    response = client.get(
        f"/api/v2/workspaces/{snapshot.workspace.name}/snapshots/{snapshot.pk}"
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_snapshot_api_unpublished_no_permission():
    snapshot = SnapshotFactory(published_at=None)

    client = APIClient()
    # logged in, but no permission
    client.force_authenticate(user=UserFactory())

    response = client.get(
        f"/api/v2/workspaces/{snapshot.workspace.name}/snapshots/{snapshot.pk}"
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_snapshot_api_unpublished_with_permission():
    snapshot = SnapshotFactory(published_at=None)

    client = APIClient()
    client.force_authenticate(user=UserFactory(roles=[ProjectCollaborator]))

    response = client.get(
        f"/api/v2/workspaces/{snapshot.workspace.name}/snapshots/{snapshot.pk}"
    )

    assert response.status_code == 200
    assert response.data == {"files": []}


@pytest.mark.django_db
def test_snapshot_create_unknown_files():
    workspace = WorkspaceFactory()
    user = UserFactory()
    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        f"/api/v2/workspaces/{workspace.name}/snapshots",
        {"file_ids": ["test"]},
    )

    assert response.status_code == 400, response.data
    assert "Unknown file IDs" in response.data["detail"], response.data


@pytest.mark.django_db
def test_snapshot_create_with_existing_snapshot():
    workspace = WorkspaceFactory()
    uploads = ReleaseUploadsFactory({"file1.txt": b"test1"})
    release = ReleaseFactory(uploads, workspace=workspace)
    snapshot = SnapshotFactory(workspace=workspace)
    snapshot.files.set(release.files.all())

    user = UserFactory()
    ProjectMembershipFactory(
        project=workspace.project, user=user, roles=[ProjectDeveloper]
    )

    client = APIClient()
    client.force_authenticate(user=user)

    data = {"file_ids": [release.files.first().pk]}
    response = client.post(f"/api/v2/workspaces/{workspace.name}/snapshots", data)

    assert response.status_code == 400, response.data

    msg = "A release with the current files already exists"
    assert msg in response.data["detail"], response.data


@pytest.mark.django_db
def test_snapshot_create_with_permission():
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

    client = APIClient()
    client.force_authenticate(user=user)

    data = {
        "file_ids": [
            release.files.get(name="file1.txt").pk,
            release.files.get(name="file3.txt").pk,
            release.files.get(name="file5.txt").pk,
        ],
    }
    response = client.post(f"/api/v2/workspaces/{workspace.name}/snapshots", data)

    assert response.status_code == 201

    workspace.refresh_from_db()

    assert workspace.snapshots.count() == 1

    snapshot_file_ids = set_from_qs(workspace.snapshots.first().files.all())
    current_file_ids = set_from_qs(workspace.files.all())
    assert snapshot_file_ids <= current_file_ids


@pytest.mark.django_db
def test_snapshot_create_without_permission():
    workspace = WorkspaceFactory()

    client = APIClient()
    client.force_authenticate(user=UserFactory())
    data = {"file_ids": ["test"]}
    response = client.post(f"/api/v2/workspaces/{workspace.name}/snapshots", data)

    assert response.status_code == 403, response.data
