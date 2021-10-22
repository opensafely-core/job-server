from django.urls import reverse

from staff.views.backends import (
    BackendDetail,
    BackendEdit,
    BackendList,
    BackendRotateToken,
)

from ....factories import BackendFactory


def test_backendedit_success(rf, core_developer):
    backend = BackendFactory()

    request = rf.post("/", {"level_4_url": "http://testing"})
    request.user = core_developer

    response = BackendEdit.as_view()(request, pk=backend.pk)

    assert response.status_code == 302
    assert response.url == backend.get_staff_url()

    backend.refresh_from_db()
    assert backend.level_4_url == "http://testing"


def test_backenddetail_success(rf, core_developer):
    backend = BackendFactory()

    request = rf.get("/")
    request.user = core_developer
    response = BackendDetail.as_view()(request, pk=backend.pk)

    assert response.status_code == 200
    assert response.context_data["backend"] == backend


def test_backendlist_success(rf, core_developer):
    BackendFactory.create_batch(3)

    request = rf.get("/")
    request.user = core_developer

    response = BackendList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 3


def test_backendrotatetoken_success(rf, core_developer):
    backend = BackendFactory()

    request = rf.post("/")
    request.user = core_developer
    response = BackendRotateToken.as_view()(request, pk=backend.pk)

    assert response.status_code == 302
    assert response.url == reverse("staff:backend-detail", kwargs={"pk": backend.pk})
