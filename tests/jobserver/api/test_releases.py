import pytest
from rest_framework.test import APIClient
from slack_sdk.errors import SlackApiError

from jobserver.api.releases import ReleaseNotificationAPICreate
from jobserver.models import Release
from tests.factories import (
    BackendFactory,
    OrgFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    ReleaseFactory,
    ReleaseUploadFactory,
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
def test_upload_api_no_workspace():
    response = APIClient().put("/api/v2/workspaces/notexists/releases/hash")
    assert response.status_code == 404


@pytest.mark.django_db
def test_upload_api_no_backend_token():
    workspace = WorkspaceFactory()
    response = APIClient().put(f"/api/v2/workspaces/{workspace.name}/releases/hash")
    assert response.status_code == 403


@pytest.mark.django_db
def test_upload_api_bad_backend_token():
    workspace = WorkspaceFactory()
    BackendFactory(auth_token="test")

    response = APIClient().put(
        f"/api/v2/workspaces/{workspace.name}/releases/hash",
        HTTP_AUTHORIZATION="invalid",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_upload_api_no_user():
    workspace = WorkspaceFactory()
    BackendFactory(auth_token="test")
    response = APIClient().put(
        f"/api/v2/workspaces/{workspace.name}/releases/hash",
        HTTP_AUTHORIZATION="test",
    )

    assert response.status_code == 403
    assert "Backend-User" in response.data["detail"]


@pytest.mark.django_db
def test_upload_api_no_files():
    workspace = WorkspaceFactory()
    BackendFactory(auth_token="test")
    response = APIClient().put(
        f"/api/v2/workspaces/{workspace.name}/releases/hash",
        HTTP_AUTHORIZATION="test",
        HTTP_BACKEND_USER="user",
    )

    assert response.status_code == 400
    assert "No data" in response.data["detail"]


@pytest.mark.django_db
def test_upload_api_created():
    org = OrgFactory()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)
    BackendFactory(auth_token="test")
    upload = ReleaseUploadFactory()

    assert Release.objects.count() == 0

    response = APIClient().put(
        f"/api/v2/workspaces/{workspace.name}/releases/{upload.hash}",
        content_type="application/octet-stream",
        data=upload.zip.read(),
        HTTP_CONTENT_DISPOSITION="attachment; filename=release.zip",
        HTTP_AUTHORIZATION="test",
        HTTP_BACKEND_USER="user",
    )

    assert response.status_code == 201
    assert Release.objects.count() == 1

    release = Release.objects.first()
    assert response["Release-Id"] == release.id
    assert response["Location"] == f"http://testserver{release.get_absolute_url()}"


@pytest.mark.django_db
def test_upload_api_redirected():
    org = OrgFactory()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)
    backend = BackendFactory(auth_token="test")
    files = {"file.txt": "test redirect"}
    upload = ReleaseUploadFactory(files)

    # release already exists
    release = ReleaseFactory(workspace=workspace, backend=backend, files=files)
    assert Release.objects.count() == 1

    response = APIClient().put(
        f"/api/v2/workspaces/{workspace.name}/releases/{upload.hash}",
        content_type="application/octet-stream",
        data=upload.zip.read(),
        HTTP_CONTENT_DISPOSITION="attachment; filename=release.zip",
        HTTP_AUTHORIZATION="test",
        HTTP_BACKEND_USER="user",
    )

    assert response.status_code == 303
    assert Release.objects.count() == 1

    release.refresh_from_db()
    assert response["Release-Id"] == release.id
    assert response["Location"] == f"http://testserver{release.get_absolute_url()}"


@pytest.mark.django_db
def test_release_index_api_not_exists():
    client = APIClient()

    # bad id
    response = client.get("/api/v2/releases/badid")
    assert response.status_code == 404


@pytest.mark.django_db
def test_release_index_api_anonymous():
    release = ReleaseFactory()
    client = APIClient()
    index_url = f"/api/v2/releases/{release.id}"

    response = client.get(index_url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_release_index_api_logged_in_no_permission():
    release = ReleaseFactory()
    user = UserFactory()
    client = APIClient()
    index_url = f"/api/v2/releases/{release.id}"

    client.force_authenticate(user=user)
    response = client.get(index_url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_release_index_api_have_permission():
    release = ReleaseFactory()
    user = UserFactory()
    client = APIClient()
    index_url = f"/api/v2/releases/{release.id}"

    ProjectMembershipFactory(user=user, project=release.workspace.project)
    client.force_authenticate(user=user)
    response = client.get(index_url)
    assert response.status_code == 200
    assert response.json() == {
        "files": [
            {
                "name": "file.txt",
                "url": f"/api/v2/releases/{release.id}/file.txt",
            }
        ],
    }


@pytest.mark.django_db
def test_release_file_api_release_not_exists():
    client = APIClient()

    response = client.get("/api/v2/releases/badid/file.txt")
    assert response.status_code == 404


@pytest.mark.django_db
def test_release_file_api_anonymous():
    release = ReleaseFactory()
    client = APIClient()
    file_url = f"/api/v2/releases/{release.id}/file.txt"

    response = client.get(file_url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_release_file_api_no_permission():
    release = ReleaseFactory()
    user = UserFactory()
    client = APIClient()
    file_url = f"/api/v2/releases/{release.id}/file.txt"

    # logged in, but no permission
    client.force_authenticate(user=user)
    response = client.get(file_url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_release_file_api_have_permission():
    release = ReleaseFactory()
    user = UserFactory()
    client = APIClient()
    file_url = f"/api/v2/releases/{release.id}/file.txt"

    # logged in, with permission
    ProjectMembershipFactory(user=user, project=release.workspace.project)
    client.force_authenticate(user=user)
    response = client.get(file_url)
    assert response.status_code == 200
    assert b"".join(response.streaming_content) == b"test"
    assert response.headers["Content-Type"] == "text/plain"


@pytest.mark.django_db
def test_release_file_api_nginx_redirect():
    release = ReleaseFactory()
    user = UserFactory()
    client = APIClient()
    file_url = f"/api/v2/releases/{release.id}/file.txt"

    # test nginx configuration
    ProjectMembershipFactory(user=user, project=release.workspace.project)
    client.force_authenticate(user=user)
    response = client.get(file_url, HTTP_RELEASES_REDIRECT="/storage")
    assert response.status_code == 200
    assert (
        response.headers["X-Accel-Redirect"]
        == f"/storage/{release.workspace.name}/releases/{release.id}/file.txt"
    )


@pytest.mark.django_db
def test_release_file_api_file_deleted():
    release = ReleaseFactory()
    user = UserFactory()
    client = APIClient()
    file_url = f"/api/v2/releases/{release.id}/file.txt"

    ProjectMembershipFactory(user=user, project=release.workspace.project)
    client.force_authenticate(user=user)

    # delete file
    release.files.get(name="file.txt").absolute_path().unlink()
    response = client.get(file_url)

    assert response.status_code == 404


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
    index_url = f"/api/v2/releases/workspace/{workspace.name}"

    client.force_authenticate(user=user)
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
    ProjectMembershipFactory(user=user, project=workspace.project)

    index_url = f"/api/v2/releases/workspace/{workspace.name}"

    release1 = ReleaseFactory(
        workspace=workspace, backend=backend1, files={"file1.txt": "backend1"}
    )
    release2 = ReleaseFactory(
        workspace=workspace, backend=backend2, files={"file1.txt": "backend2"}
    )

    response = client.get(index_url)
    assert response.status_code == 200
    assert response.json() == {
        "files": [
            {
                "name": "backend2/file1.txt",
                "url": f"/api/v2/releases/{release2.id}/file1.txt",
            },
            {
                "name": "backend1/file1.txt",
                "url": f"/api/v2/releases/{release1.id}/file1.txt",
            },
        ],
    }
