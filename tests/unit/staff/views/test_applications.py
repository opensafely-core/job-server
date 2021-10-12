import pytest
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import Http404
from django.utils import timezone

from jobserver.utils import set_from_qs
from staff.views.applications import ApplicationDetail, ApplicationList

from ....factories import ApplicationFactory, UserFactory


def test_applicationdetail_success_with_complete_application(
    rf, core_developer, complete_application
):
    application = complete_application
    page = application.contactdetailspage
    page.full_name = "Mickey Mouse"
    page.save()

    request = rf.get("/")
    request.user = core_developer

    response = ApplicationDetail.as_view()(request, pk_hash=application.pk_hash)

    assert response.status_code == 200
    assert response.context_data["pages"][0]["title"] == "Contact details"
    assert response.context_data["pages"][0]["started"] is True
    assert "Mickey Mouse" in response.rendered_content
    assert "User has not started this page" not in response.rendered_content


def test_applicationdetail_success_with_incomplete_application(
    rf, core_developer, incomplete_application
):
    application = incomplete_application
    page = application.contactdetailspage
    page.full_name = "Mickey Mouse"
    page.save()

    request = rf.get("/")
    request.user = core_developer

    response = ApplicationDetail.as_view()(request, pk_hash=application.pk_hash)

    assert response.status_code == 200
    assert response.context_data["pages"][0]["title"] == "Contact details"
    assert response.context_data["pages"][0]["started"] is True
    assert "Mickey Mouse" in response.rendered_content
    assert "User has not started this page" in response.rendered_content


def test_applicationdetail_with_unknown_user(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(Http404):
        ApplicationDetail.as_view()(request, pk_hash="0000")


def test_applicationdetail_without_core_dev_role(rf):
    application = ApplicationFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ApplicationDetail.as_view()(request, pk_hash=application.pk_hash)


def test_applicationdetail_post_with_complete_application(
    rf,
    core_developer,
    complete_application,
    freezer,
):
    application = complete_application

    application.contactdetailspage.last_reviewed_at = None
    application.contactdetailspage.reviewed_by = None
    application.studyinformationpage.last_reviewed_at = None
    application.studyinformationpage.reviewed_by = None

    data = {
        "contact-details-notes": "could do better",
        "contact-details-is_approved": "False",
        "study-information-notes": "couldn't do better",
        "study-information-is_approved": "True",
    }

    request = rf.post("/", data)
    request.user = core_developer

    response = ApplicationDetail.as_view()(request, pk_hash=application.pk_hash)

    assert response.status_code == 302

    application.refresh_from_db()

    assert application.contactdetailspage.notes == "could do better"
    assert application.contactdetailspage.is_approved is False
    assert application.studyinformationpage.notes == "couldn't do better"
    assert application.studyinformationpage.is_approved is True

    now = timezone.now()
    assert application.contactdetailspage.last_reviewed_at == now
    assert application.contactdetailspage.reviewed_by == request.user
    assert application.studyinformationpage.last_reviewed_at == now
    assert application.studyinformationpage.reviewed_by == request.user


def test_applicationdetail_post_with_incomplete_application(
    rf,
    core_developer,
    incomplete_application,
    freezer,
):
    application = incomplete_application

    application.contactdetailspage.last_reviewed_at = None
    application.contactdetailspage.reviewed_by = None
    application.studyinformationpage.last_reviewed_at = None
    application.studyinformationpage.reviewed_by = None

    data = {
        "contact-details-notes": "could do better",
        "contact-details-is_approved": "False",
        "study-information-notes": "couldn't do better",
        "study-information-is_approved": "True",
    }

    request = rf.post("/", data)
    request.user = core_developer

    response = ApplicationDetail.as_view()(request, pk_hash=application.pk_hash)

    assert response.status_code == 302

    application.refresh_from_db()
    assert application.contactdetailspage.notes == "could do better"
    assert application.contactdetailspage.is_approved is False
    assert application.studyinformationpage.notes == "couldn't do better"
    assert application.studyinformationpage.is_approved is True

    now = timezone.now()
    assert application.contactdetailspage.last_reviewed_at == now
    assert application.contactdetailspage.reviewed_by == request.user
    assert application.studyinformationpage.last_reviewed_at == now
    assert application.studyinformationpage.reviewed_by == request.user

    # Check that a page instance has not been created
    with pytest.raises(ObjectDoesNotExist):
        application.researcherdetailspage


def test_applicationlist_search(rf, core_developer):
    app1 = ApplicationFactory(created_by=UserFactory(first_name="ben"))
    app2 = ApplicationFactory(created_by=UserFactory(username="ben"))
    ApplicationFactory(created_by=UserFactory(username="seb"))

    request = rf.get("/?q=ben")
    request.user = core_developer

    response = ApplicationList.as_view()(request)

    assert response.status_code == 200

    assert len(response.context_data["object_list"]) == 2
    assert set_from_qs(response.context_data["object_list"]) == {app1.pk, app2.pk}


def test_applicationlist_success(rf, core_developer):
    ApplicationFactory.create_batch(5)

    request = rf.get("/")
    request.user = core_developer

    response = ApplicationList.as_view()(request)

    assert response.status_code == 200

    assert len(response.context_data["object_list"]) == 5
