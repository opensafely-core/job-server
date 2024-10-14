import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied

from staff.views import sentry
from staff.views.sentry import sentry_sdk


def test_error_success(rf, staff_area_administrator):
    request = rf.get("/")
    request.user = staff_area_administrator

    with pytest.raises(ZeroDivisionError):
        sentry.error(request)


def test_error_unauthorized(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        sentry.error(request)


def test_index_success(rf, staff_area_administrator):
    request = rf.get("/")
    request.user = staff_area_administrator

    response = sentry.index(request)

    assert response.status_code == 200


def test_index_unauthorized(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        sentry.index(request)


def test_message_success(rf, staff_area_administrator, mocker):
    request = rf.get("/")
    request.user = staff_area_administrator

    spy = mocker.spy(sentry_sdk, "capture_message")

    response = sentry.message(request)

    assert response.status_code == 200
    spy.assert_called_once_with("testing")


def test_message_unauthorized(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        sentry.message(request)
