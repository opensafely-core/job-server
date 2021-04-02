import pytest

from jobserver.authorization.decorators import require_superuser

from ...factories import UserFactory


@pytest.mark.django_db
def test_require_superuser_with_core_dev_role(rf, superuser):
    request = rf.get("/")
    request.user = superuser

    def dispatch(request):
        return request

    returned_request = require_superuser(dispatch)(request)

    # check the request is passed through the decorator
    assert returned_request == request


@pytest.mark.django_db
def test_require_superuser_without_core_dev_role(rf):
    request = rf.get("/")
    request.user = UserFactory(roles=[])

    response = require_superuser(None)(request)

    assert response.status_code == 403
