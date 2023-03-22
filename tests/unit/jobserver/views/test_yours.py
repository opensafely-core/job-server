from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from jobserver.utils import set_from_qs
from jobserver.views.yours import AnalysisRequestList, ProjectList

from ....factories import (
    AnalysisRequestFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    UserFactory,
)


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


def test_projectlist_success(rf):
    user = UserFactory()

    ProjectFactory.create_batch(3, created_by=user)
    ProjectFactory.create_batch(3)

    m1 = ProjectMembershipFactory(user=user)
    m2 = ProjectMembershipFactory(user=user)

    request = rf.get("/")
    request.user = user

    response = ProjectList.as_view()(request)

    assert response.status_code == 200

    assert set_from_qs(response.context_data["object_list"]) == {
        m1.project.pk,
        m2.project.pk,
    }


def test_projectlist_unauthorized(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    response = ProjectList.as_view()(request)

    assert response.status_code == 302
    assert response.url == f"{settings.LOGIN_URL}?next={settings.LOGIN_REDIRECT_URL}"
