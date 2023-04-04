from django.contrib.auth.models import AnonymousUser
from django.test.utils import override_settings

from jobserver.middleware import ClientAddressIdentification, RequireNameMiddleware

from ...factories import BackendFactory, UserFactory


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
    assert response.url == "/settings/?next=/"


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


@override_settings(BACKEND_IP_MAP={"1.2.3.4": "tpp"})
def test_client_ip_middleware_remote_addr(rf):
    backend = BackendFactory(slug="tpp")
    mw = ClientAddressIdentification(lambda r: None)

    request = rf.get("/")
    request.META["REMOTE_ADDR"] = "4.3.2.1"
    mw(request)
    assert request.backend is None

    request = rf.get("/")
    request.META["REMOTE_ADDR"] = "1.2.3.4"
    mw(request)
    assert request.backend == backend


@override_settings(BACKEND_IP_MAP={"1.2.3.4": "tpp"}, TRUSTED_PROXIES=["172.17.0.2"])
def test_client_ip_middleware_proxied(rf):
    backend = BackendFactory(slug="tpp")
    mw = ClientAddressIdentification(lambda r: None)
    proxy = "172.17.0.2"

    # not tpp client
    request = rf.get("/")
    request.META["HTTP_X_FORWARDED_FOR"] = "4.3.2.1"
    request.META["REMOTE_ADDR"] = proxy
    mw(request)
    assert request.backend is None

    # tpp client
    request = rf.get("/")
    request.META["HTTP_X_FORWARDED_FOR"] = "1.2.3.4"
    request.META["REMOTE_ADDR"] = proxy
    mw(request)
    assert request.backend == backend

    # test spoofing header doesn't work
    request = rf.get("/")
    # attacker submits request with X-Forwarded-For already set to TPP address.
    # Our proxy adds the actualy addres to the header. But we should only trust
    # the actual address, not the spoofed one
    request.META["HTTP_X_FORWARDED_FOR"] = "1.2.3.4,4.3.2.1"
    request.META["REMOTE_ADDR"] = proxy
    mw(request)
    assert request.backend is None
