import pytest

from applications.views import application

from ...factories import UserFactory


@pytest.mark.django_db
def test_get_application(rf):
    request = rf.get("/")
    request.user = UserFactory()
    response = application(request)
    assert response.status_code == 200
