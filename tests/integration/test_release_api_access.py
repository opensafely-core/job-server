from django.urls import reverse
from django.utils import timezone

from ..factories import (
    SnapshotFactory,
    SnapshotPublishRequest,
    SnapshotPublishRequestFactory,
    UserFactory,
    WorkspaceFactory,
)


def test_published_output_access(client, release):
    user = UserFactory()
    workspace = WorkspaceFactory()
    snapshot = SnapshotFactory(workspace=workspace)
    snapshot.files.set(release.files.all())
    SnapshotPublishRequestFactory(
        snapshot=snapshot,
        decision=SnapshotPublishRequest.Decisions.APPROVED,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
    )

    response = client.get(snapshot.get_api_url())
    assert response.status_code == 200

    user = UserFactory()
    token = user.rotate_token()

    response = client.get(
        snapshot.get_api_url(),
        HTTP_AUTHORIZATION=f"{user.username}:{token}",
    )
    assert response.status_code == 200


def test_unpublished_output_access(client, release):
    workspace = WorkspaceFactory()
    snapshot = SnapshotFactory(workspace=workspace)
    snapshot.files.set(release.files.all())

    user = UserFactory()
    token = user.rotate_token()

    url = reverse("api:release-file", kwargs={"file_id": release.files.first().id})

    response = client.get(url)
    assert response.status_code == 403, response.content

    response = client.get(url, HTTP_AUTHORIZATION=f"{user.username}:{token}")
    assert response.status_code == 200, response.content
