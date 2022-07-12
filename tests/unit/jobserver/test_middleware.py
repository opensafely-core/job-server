from django.contrib.auth.models import AnonymousUser

from jobserver.middleware import RequireNameMiddleware

from ...factories import UserFactory


def get_response(request):
    return "no match"


def test_requirenamemiddleware_with_fullname_set(rf):
    request = rf.get("/")
    request.user = UserFactory(fullname="Ben Goldacre")

    response = RequireNameMiddleware(get_response)(request)

    assert response == "no match"


def test_requirenamemiddleware_without_fullname_set(rf):
    request = rf.get("/")
    request.user = UserFactory(fullname="")

    response = RequireNameMiddleware(get_response)(request)

    assert response.status_code == 302


def test_requirenamemiddleware_with_exempt_url(rf):
    request = rf.get("/staff")
    request.user = UserFactory(fullname="")

    response = RequireNameMiddleware(get_response)(request)

    assert response == "no match"


def test_requirenamemiddleware_with_unauthenticated_user(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    response = RequireNameMiddleware(get_response)(request)

    assert response == "no match"
