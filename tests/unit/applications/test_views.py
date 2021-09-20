from django.urls import reverse

from applications.models import Application
from applications.views import terms


def test_terms_get_success(rf):
    request = rf.get("/")

    response = terms(request)

    assert response.status_code == 200


def test_terms_post_success(rf):
    request = rf.post("/")

    assert Application.objects.count() == 0

    response = terms(request)

    assert response.status_code == 302

    application = Application.objects.first()
    expected_url = reverse(
        "applications:page", kwargs={"pk": application.pk, "page_num": 1}
    )
    assert response.url == expected_url
