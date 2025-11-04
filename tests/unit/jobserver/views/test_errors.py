from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import TooManyFieldsSent

from jobserver.views.errors import (
    bad_request,
    csrf_failure,
    page_not_found,
    permission_denied,
    server_error,
)


def test_bad_request(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    response = bad_request(request)

    assert response.status_code == 400
    assert "Bad request" in response.rendered_content
    assert "An error has occurred displaying this page." in response.rendered_content


def test_bad_request_too_many_fields(rf):
    request = rf.post("/")
    request.user = AnonymousUser()

    response = bad_request(request, exception=TooManyFieldsSent("Too many fields"))

    assert response.status_code == 413
    assert "Too many fields submitted" in response.rendered_content
    assert (
        "Your submission contained too many fields. Please reduce the number of selected items and try again."
        in response.rendered_content
    )


def test_csrf_failure(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    response = csrf_failure(request)

    assert response.status_code == 400
    assert "CSRF Failed" in response.rendered_content
    assert "The form was not able to submit." in response.rendered_content


def test_permission_denied(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    response = permission_denied(request)

    assert response.status_code == 403
    assert "Permission denied" in response.rendered_content
    assert (
        "You do not have permission to access this page." in response.rendered_content
    )


def test_page_not_found(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    response = page_not_found(request)

    assert response.status_code == 404
    assert "Page not found" in response.rendered_content
    assert "Please check the URL in the address bar." in response.rendered_content


def test_server_error(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    response = server_error(request)

    assert response.status_code == 500
    assert "Server error" in response.rendered_content
    assert "An error has occurred displaying this page." in response.rendered_content
