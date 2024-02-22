from django.contrib.auth.models import AnonymousUser

from jobserver.views.health_check import HealthCheck


def test_health_check_successful(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    response = HealthCheck.as_view()(request)

    assert response.status_code == 200
