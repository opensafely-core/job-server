import pytest
from django.urls import reverse

from jobserver.views.backends import BackendDetail, BackendList, BackendRotateToken

from ...factories import BackendFactory


MEANINGLESS_URL = "/"


@pytest.mark.django_db
def test_backenddetail_success(rf, superuser):
    backend = BackendFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser
    response = BackendDetail.as_view()(request, pk=backend.pk)

    assert response.status_code == 200
    assert response.context_data["backend"] == backend


@pytest.mark.django_db
def test_backendlist_success(rf, superuser):
    request = rf.get(MEANINGLESS_URL)
    request.user = superuser
    response = BackendList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 6


@pytest.mark.django_db
def test_backendrotatetoken_success(rf, superuser):
    backend = BackendFactory()

    request = rf.post(MEANINGLESS_URL)
    request.user = superuser
    response = BackendRotateToken.as_view()(request, pk=backend.pk)

    assert response.status_code == 302
    assert response.url == reverse("backend-detail", kwargs={"pk": backend.pk})
