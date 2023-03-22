from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from jobserver.views.yours import AnalysisRequestList

from ....factories import AnalysisRequestFactory, UserFactory


def test_analysisrequestlist_success(rf):
    user = UserFactory()

    AnalysisRequestFactory.create_batch(3, created_by=user)
    AnalysisRequestFactory.create_batch(3)

    request = rf.get("/")
    request.user = user

    response = AnalysisRequestList.as_view()(request)

    assert response.status_code == 200

    assert len(response.context_data["object_list"]) == 3


def test_analysisrequestlist_unauthorized(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    response = AnalysisRequestList.as_view()(request)

    assert response.status_code == 302
    assert response.url == f"{settings.LOGIN_URL}?next={settings.LOGIN_REDIRECT_URL}"
