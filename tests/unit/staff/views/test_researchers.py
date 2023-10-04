import pytest
from django.core.exceptions import PermissionDenied
from django.http import Http404

from staff.views.researchers import ResearcherEdit

from ....factories import ApplicationFactory, ResearcherRegistrationFactory, UserFactory


def test_researcheredit_get_success(rf, core_developer):
    application = ApplicationFactory()
    researcher = ResearcherRegistrationFactory(application=application)

    request = rf.get("/")
    request.user = core_developer

    response = ResearcherEdit.as_view()(
        request,
        pk_hash=application.pk_hash,
        pk=researcher.pk,
    )

    assert response.status_code == 200


def test_researcheredit_post_success(rf, core_developer):
    application = ApplicationFactory()
    researcher = ResearcherRegistrationFactory(application=application)

    data = {
        "name": "name",
        "job_title": "job title",
        "email": "test@example.com",
        "github_username": "new username",
        "daa": "http://example.com",
    }
    request = rf.post("/", data)
    request.user = core_developer

    response = ResearcherEdit.as_view()(
        request,
        pk_hash=application.pk_hash,
        pk=researcher.pk,
    )

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == researcher.application.get_staff_url()

    researcher.refresh_from_db()
    assert researcher.name == "name"
    assert researcher.job_title == "job title"
    assert researcher.email == "test@example.com"
    assert researcher.github_username == "new username"
    assert researcher.daa == "http://example.com"


def test_researcheredit_unknown_application(rf, core_developer):
    researcher = ResearcherRegistrationFactory()

    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(Http404):
        ResearcherEdit.as_view()(request, pk_hash="", pk=researcher.pk)


def test_researcheredit_unknown_researcher(rf, core_developer):
    application = ApplicationFactory()

    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(Http404):
        ResearcherEdit.as_view()(request, pk_hash=application.pk_hash, pk=0)


def test_researcheredit_without_core_dev_role(rf, core_developer):
    application = ApplicationFactory()
    researcher = ResearcherRegistrationFactory(application=application)

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ResearcherEdit.as_view()(
            request,
            pk_hash=application.pk_hash,
            pk=researcher.pk,
        )
