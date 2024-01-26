from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.test.utils import override_settings
from django.views.generic import DetailView, View

from jobserver.middleware import ClientAddressIdentification, TemplateNameMiddleware
from jobserver.models import Project

from ...factories import BackendFactory, ProjectFactory


@override_settings(BACKEND_IP_MAP={"1.2.3.4": "tpp"})
def test_client_ip_middleware_remote_addr(rf):
    backend = BackendFactory(slug="tpp")
    middleware = ClientAddressIdentification(lambda r: None)

    request = rf.get("/", REMOTE_ADDR="4.3.2.1")
    middleware(request)
    assert request.backend is None

    request = rf.get("/", REMOTE_ADDR="1.2.3.4")
    middleware(request)
    assert request.backend == backend


@override_settings(BACKEND_IP_MAP={"1.2.3.4": "tpp"}, TRUSTED_PROXIES=["172.17.0."])
def test_client_ip_middleware_proxied(rf):
    backend = BackendFactory(slug="tpp")
    middleware = ClientAddressIdentification(lambda r: None)
    proxy = "172.17.0.2"

    # not tpp client
    request = rf.get("/", headers={"x-forwarded-for": "4.3.2.1"}, REMOTE_ADDR=proxy)
    middleware(request)
    assert request.backend is None

    # tpp client
    request = rf.get("/", headers={"x-forwarded-for": "1.2.3.4"}, REMOTE_ADDR=proxy)
    middleware(request)
    assert request.backend == backend

    # test spoofing header doesn't work
    # attacker submits request with X-Forwarded-For already set to TPP address.
    # Our proxy adds the actualy addres to the header. But we should only trust
    # the actual address, not the spoofed one
    request = rf.get(
        "/", headers={"x-forwarded-for": "1.2.3.4,4.3.2.1"}, REMOTE_ADDR=proxy
    )
    middleware(request)
    assert request.backend is None

    # test spoofing header doesn't work
    # attacker attempts to spoof both the TPP address & the proxy address
    request = rf.get(
        "/",
        headers={"x-forwarded-for": "1.2.3.4,172.17.0.2,4.3.2.1"},
        REMOTE_ADDR=proxy,
    )
    middleware(request)
    assert request.backend is None


@override_settings(
    BACKEND_IP_MAP={"1.2.3.4": "tpp"}, TRUSTED_PROXIES=["172.17.0.", "103.21.244."]
)
def test_client_ip_middleware_proxied_twice(rf):
    backend = BackendFactory(slug="tpp")
    middleware = ClientAddressIdentification(lambda r: None)
    proxy = "172.17.0.2"

    # tpp client via proxy
    request = rf.get(
        "/", headers={"x-forwarded-for": "1.2.3.4,103.21.244.16"}, REMOTE_ADDR=proxy
    )
    middleware(request)
    assert request.backend == backend


@override_settings(TRUSTED_PROXIES=["172.17.0."])
def test_client_ip_middleware_get_forwarded_ip_no_ips():
    middleware = ClientAddressIdentification(None)
    # no ips in header, just return direct client ip
    assert (
        middleware.get_forwarded_ip(
            "",
            "172.17.0.2",
            ["172.17.0."],
        )
        == "172.17.0.2"
    )


def test_template_name_middleware_with_no_context_data(rf):
    def dummy_view(request):
        response = HttpResponse()
        response.context_data = None
        return response

    request = rf.get("/")
    response = dummy_view(request)

    assert response.context_data is None

    TemplateNameMiddleware(None).process_template_response(request, response)

    # context_data is None should be a no-op for the middleware
    assert response.context_data is None


def test_template_name_middleware_with_template_name_already_in_context(rf):
    def dummy_view(request):
        return TemplateResponse(request, "")

    request = rf.get("/")
    response = dummy_view(request)

    template_name = getattr(response, "template_name", "already set")

    TemplateNameMiddleware(None).process_template_response(request, response)

    # when template_name is already set it should not be changed by the middleware
    assert response.template_name == template_name


def test_template_name_middleware_with_template_name_as_a_list(rf):
    project = ProjectFactory()

    class DummyView(DetailView):
        model = Project
        template_name = "my_template"

    request = rf.get("/")
    response = DummyView.as_view()(request, pk=project.pk)

    TemplateNameMiddleware(None).process_template_response(request, response)

    assert response.context_data["template_name"] == "my_template"


def test_template_name_middleware_with_template_name_as_a_string(rf):
    class DummyView(View):
        def get(self, request, *args, **kwargs):
            return TemplateResponse(request, "my_template", context={})

    request = rf.get("/")
    response = DummyView.as_view()(request)

    TemplateNameMiddleware(None).process_template_response(request, response)

    assert response.context_data["template_name"] == "my_template"
