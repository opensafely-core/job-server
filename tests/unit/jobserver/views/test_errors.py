from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import TooManyFieldsSent

from jobserver.views.errors import (
    bad_request,
    csrf_failure,
    page_not_found,
    permission_denied,
    server_error,
)

from ....factories import UserFactory


def test_bad_request(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    response = bad_request(request)

    assert response.status_code == 400
    assert "Bad request" in response.rendered_content
    assert "An error occurred while displaying this page." in response.rendered_content


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
    assert "The form could not be submitted." in response.rendered_content


def test_permission_denied_for_anonymous_user(rf):
    request = rf.get("/test/")
    request.user = AnonymousUser()

    response = permission_denied(request)

    assert response.status_code == 403
    assert "Permission denied" in response.rendered_content
    assert "you need to log in" in response.rendered_content.lower()
    assert (
        "your account does not have the required permissions"
        in response.rendered_content.lower()
    )
    assert 'id="error-page-login-button"' in response.rendered_content


def test_permission_denied_for_authenticated_user(rf):
    request = rf.get("/test/")
    request.user = UserFactory()

    response = permission_denied(request)

    assert response.status_code == 403
    assert "Permission denied" in response.rendered_content
    assert "you need to log in" not in response.rendered_content.lower()
    assert 'id="error-page-login-button"' not in response.rendered_content


def test_page_not_found_for_anonymous_user(rf):
    request = rf.get("/test/")
    request.user = AnonymousUser()

    response = page_not_found(request)

    assert response.status_code == 404
    assert "Page not found" in response.rendered_content
    assert "<p>This may be because:</p>" in response.rendered_content
    assert "<li>the link is incorrect</li>" in response.rendered_content
    assert "you need to log in" in response.rendered_content.lower()
    assert 'id="error-page-login-button"' in response.rendered_content


def test_page_not_found_for_authenticated_user(rf):
    request = rf.get("/test/")
    request.user = UserFactory()

    response = page_not_found(request)

    assert response.status_code == 404
    assert "Page not found" in response.rendered_content
    assert "you need to log in" not in response.rendered_content.lower()
    assert 'id="error-page-login-button"' not in response.rendered_content


def test_server_error(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    response = server_error(request)

    assert response.status_code == 500
    assert "Server error" in response.rendered_content
    assert "An error occurred while displaying this page." in response.rendered_content
