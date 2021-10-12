from django.contrib.auth.decorators import login_required
from django.test.utils import override_settings
from django.urls import path

from jobserver.urls import urlpatterns as base_urlpatterns


@login_required
def view_fn(request):
    return "Hello"  # pragma: no cover


urlpatterns = [path("test/", view_fn, name="test")] + base_urlpatterns


@override_settings(ROOT_URLCONF=__name__)
def test_login_required_redirect(client):
    response = client.get("/test/", follow=True)
    assert response.status_code == 200
    assert response.redirect_chain == [("/login/?next=/test/", 302)]
