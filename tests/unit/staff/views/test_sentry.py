import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied

from staff.views import sentry
from staff.views.sentry import sentry_sdk


def test_error_success(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(ZeroDivisionError):
        sentry.error(request)


def test_error_unauthorized(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        sentry.error(request)


def test_index_success(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    response = sentry.index(request)

    assert response.status_code == 200


def test_index_unauthorized(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        sentry.index(request)


def test_message_success(rf, core_developer, mocker):
    request = rf.get("/")
    request.user = core_developer

    spy = mocker.spy(sentry_sdk, "capture_message")

    response = sentry.message(request)

    assert response.status_code == 200
    spy.assert_called_once_with("testing")


def test_message_unauthorized(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        sentry.message(request)
