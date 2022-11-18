from django.contrib.auth.models import AnonymousUser

from jobserver.views.components import components


def test_components_gallery(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    response = components(request)

    assert response.status_code == 200
