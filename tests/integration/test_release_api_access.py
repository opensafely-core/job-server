from django.urls import reverse
from django.utils import timezone

from ..factories import (
    PublishRequest,
    PublishRequestFactory,
    SnapshotFactory,
    UserFactory,
    WorkspaceFactory,
)


def test_published_output_access(client, release):
    user = UserFactory()
    workspace = WorkspaceFactory()
    snapshot = SnapshotFactory(workspace=workspace)
    snapshot.files.set(release.files.all())
    PublishRequestFactory(
        snapshot=snapshot,
        decision=PublishRequest.Decisions.APPROVED,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
    )

    response = client.get(snapshot.get_api_url())
    assert response.status_code == 200

    user = UserFactory()
    token = user.rotate_token()

    response = client.get(
        snapshot.get_api_url(),
        headers={
            "authorization": f"{user.username}:{token}",
        },
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

    response = client.get(url, headers={"authorization": f"{user.username}:{token}"})
    assert response.status_code == 200, response.content
