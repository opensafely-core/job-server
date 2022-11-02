import pytest
from django.core.exceptions import PermissionDenied

from staff.views.dashboards.copiloting import Copiloting

from .....factories import UserFactory


def test_copiloting_success(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    response = Copiloting.as_view()(request)

    assert response.status_code == 200


def test_copiloting_unauthorized(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        Copiloting.as_view()(request)
