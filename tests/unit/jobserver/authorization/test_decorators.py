import pytest
from django.core.exceptions import PermissionDenied

from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_manage_backends, require_role

from ....factories import UserFactory


def test_require_manage_backends_with_core_dev_role(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    def dispatch(request):
        return request

    returned_request = require_manage_backends(dispatch)(request)

    # check the request is passed through the decorator
    assert returned_request == request


def test_require_manage_backends_without_core_dev_role(rf):
    request = rf.get("/")
    request.user = UserFactory(roles=[])

    with pytest.raises(PermissionDenied):
        require_manage_backends(None)(request)


def test_require_role_success(rf):
    request = rf.get("/")
    request.user = UserFactory(roles=[CoreDeveloper])

    def dispatch(request):
        return request

    returned_request = require_role(CoreDeveloper)(dispatch)(request)

    assert returned_request == request


def test_require_role_without_role(rf):
    request = rf.get("/")
    request.user = UserFactory(roles=[])

    with pytest.raises(PermissionDenied):
        require_role(CoreDeveloper)(None)(request)
