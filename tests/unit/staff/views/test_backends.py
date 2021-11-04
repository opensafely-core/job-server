from django.urls import reverse

from jobserver.models import Backend
from staff.views.backends import (
    BackendCreate,
    BackendDetail,
    BackendEdit,
    BackendList,
    BackendRotateToken,
)

from ....factories import BackendFactory


def test_backendcreate_get_success(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    response = BackendCreate.as_view()(request)

    assert response.status_code == 200


def test_backendcreate_post_success(rf, core_developer):
    data = {
        "name": "New Backend",
        "slug": "new-backend",
    }
    request = rf.post("/", data)
    request.user = core_developer

    response = BackendCreate.as_view()(request)

    assert response.status_code == 302, response.context_data["form"].errors

    backends = Backend.objects.all()
    assert len(backends) == 1

    backend = backends.first()
    assert backend.name == "New Backend"
    assert backend.slug == "new-backend"
    assert backend.auth_token
    assert response.url == backend.get_staff_url()


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
