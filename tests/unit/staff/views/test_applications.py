import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from applications.models import Application
from jobserver.models import Org
from jobserver.utils import set_from_qs
from staff.views.applications import (
    ApplicationApprove,
    ApplicationDetail,
    ApplicationEdit,
    ApplicationList,
    ApplicationRemove,
    ApplicationRestore,
    application_add_org,
)

from ....factories import ApplicationFactory, OrgFactory, UserFactory


def test_applicationaddorg_get_success(rf, core_developer):
    application = ApplicationFactory()

    request = rf.get("/")
    request.htmx = True
    request.user = core_developer

    response = application_add_org(request, pk_hash=application.pk_hash)

    assert response.status_code == 200
    assert "modal" in response.rendered_content


def test_applicationaddorg_post_existing_org(rf, core_developer):
    application = ApplicationFactory()
    org = OrgFactory()

    request = rf.post("/", {"name": org.name})
    request.htmx = True
    request.user = core_developer

    response = application_add_org(request, pk_hash=application.pk_hash)

    assert response.status_code == 200
    assert response.context_data["form"].errors


def test_applicationaddorg_post_success(rf, core_developer):
    application = ApplicationFactory()

    request = rf.post("/", {"name": "Test Org"})
    request.htmx = True
    request.user = core_developer

    response = application_add_org(request, pk_hash=application.pk_hash)

    assert response.status_code == 200

    destination = application.get_approve_url() + "?org-slug=test-org"
    assert response.headers["HX-Redirect"] == destination

    assert Org.objects.filter(name="Test Org").exists()


def test_applicationaddorg_unknown_application(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(Http404):
        application_add_org(request, pk_hash="test")


def test_applicationaddorg_without_core_dev_role(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        application_add_org(request)


def test_applicationaddorg_without_htmx(rf, core_developer):
    application = ApplicationFactory()

    request = rf.get("/")
    request.htmx = False
    request.user = core_developer

    response = application_add_org(request, pk_hash=application.pk_hash)

    assert response.status_code == 302
    assert response.url == application.get_approve_url()


def test_applicationapprove_already_approved(rf, core_developer, complete_application):
    complete_application.approved_at = timezone.now()
    complete_application.approved_by = core_developer
    complete_application.save()

    request = rf.get("/")
    request.user = core_developer

    response = ApplicationApprove.as_view()(
        request, pk_hash=complete_application.pk_hash
    )

    assert response.status_code == 302
    assert response.url == complete_application.get_staff_url()


def test_applicationapprove_get_success(rf, core_developer, complete_application):
    request = rf.get("/")
    request.user = core_developer

    response = ApplicationApprove.as_view()(
        request, pk_hash=complete_application.pk_hash
    )

    assert response.status_code == 200
    assert response.context_data["application"] == complete_application
    assert response.context_data["form"]["org"].initial is None


def test_applicationapprove_get_with_org_slug(rf, core_developer, complete_application):
    org = OrgFactory()

    request = rf.get("/", {"org-slug": org.slug})
    request.user = core_developer

    response = ApplicationApprove.as_view()(
        request, pk_hash=complete_application.pk_hash
    )

    assert response.status_code == 200
    assert response.context_data["application"] == complete_application
    assert response.context_data["form"]["org"].initial == org


def test_applicationapprove_get_with_org_slug_and_unknown_org(
    rf, core_developer, complete_application
):
    request = rf.get("/", {"org-slug": "0"})
    request.user = core_developer

    response = ApplicationApprove.as_view()(
        request, pk_hash=complete_application.pk_hash
    )

    assert response.status_code == 200
    assert response.context_data["application"] == complete_application
    assert response.context_data["form"]["org"].initial is None


def test_applicationapprove_post_success(rf, core_developer, complete_application):
    assert complete_application.approved_at is None
    assert complete_application.approved_by is None

    org = OrgFactory()

    data = {
        "project_name": complete_application.studyinformationpage.study_name,
        "org": str(org.pk),
    }
    request = rf.post("/", data)
    request.user = core_developer

    response = ApplicationApprove.as_view()(
        request, pk_hash=complete_application.pk_hash
    )

    assert response.status_code == 302, response.context_data["form"].errors

    complete_application.refresh_from_db()

    assert complete_application.approved_at
    assert complete_application.approved_by == core_developer
    assert complete_application.project
    assert complete_application.project.created_by == core_developer


def test_applicationapprove_with_deleted_application(
    rf, core_developer, complete_application
):
    application = complete_application
    application.deleted_at = timezone.now()
    application.deleted_by = core_developer
    application.save()

    request = rf.get("/")
    request.user = core_developer

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = ApplicationApprove.as_view()(request, pk_hash=application.pk_hash)

    assert response.status_code == 302
    assert response.url == reverse("staff:application-list")

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    msg = f"Application {complete_application.pk_hash} has been deleted, you need to restore it before you can approve it."
    assert str(messages[0]) == msg


def test_applicationapprove_with_unknown_application(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(Http404):
        ApplicationApprove.as_view()(request, pk_hash="")


def test_applicationapprove_without_study_information_page(rf, core_developer):
    application = ApplicationFactory()

    request = rf.get("/")
    request.user = core_developer

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = ApplicationApprove.as_view()(request, pk_hash=application.pk_hash)

    assert response.status_code == 302
    assert response.url == application.get_staff_url()

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    msg = "The Study Information page must be filled in before an Application can be approved."
    assert str(messages[0]) == msg


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


def test_applicationdetail_with_deleted_application(
    rf, core_developer, complete_application
):
    application = complete_application
    application.deleted_at = timezone.now()
    application.deleted_by = core_developer
    application.save()

    request = rf.get("/")
    request.user = core_developer

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = ApplicationDetail.as_view()(request, pk_hash=application.pk_hash)

    assert response.status_code == 302
    assert response.url == reverse("staff:application-list")

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    msg = f"Application {complete_application.pk_hash} has been deleted, you need to restore it before you can view it."
    assert str(messages[0]) == msg


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


def test_userlist_filter_by_status(rf, core_developer):
    ApplicationFactory(status=Application.Statuses.APPROVED_FULLY)

    request = rf.get("/?status=approved_fully")
    request.user = core_developer

    response = ApplicationList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


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


def test_applicationedit_get_success(rf, core_developer):
    application = ApplicationFactory()

    request = rf.get("/")
    request.user = core_developer

    response = ApplicationEdit.as_view()(request, pk_hash=application.pk_hash)

    assert response.status_code == 200


def test_applicationedit_post_success(rf, core_developer):
    application = ApplicationFactory(status=Application.Statuses.ONGOING)

    data = {
        "status": Application.Statuses.COMPLETED,
        "status_comment": "Completed and ready for review",
    }
    request = rf.post("/", data)
    request.user = core_developer

    response = ApplicationEdit.as_view()(request, pk_hash=application.pk_hash)

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == application.get_staff_url()

    application.refresh_from_db()
    assert application.status == Application.Statuses.COMPLETED
    assert application.status_comment == "Completed and ready for review"


def test_applicationedit_unknown_application(rf, core_developer):
    request = rf.get("/")
    request.user = core_developer

    with pytest.raises(Http404):
        ApplicationEdit.as_view()(request, pk_hash="")


def test_applicationedit_with_deleted_application(
    rf, core_developer, complete_application
):
    application = complete_application
    application.deleted_at = timezone.now()
    application.deleted_by = core_developer
    application.save()

    request = rf.get("/")
    request.user = core_developer

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = ApplicationEdit.as_view()(request, pk_hash=application.pk_hash)

    assert response.status_code == 302
    assert response.url == reverse("staff:application-list")

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    msg = f"Application {complete_application.pk_hash} has been deleted, you need to restore it before you can edit it."
    assert str(messages[0]) == msg


def test_applicationedit_without_core_dev_role(rf):
    application = ApplicationFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ApplicationEdit.as_view()(request, pk_hash=application.pk_hash)


def test_applicationlist_success(rf, core_developer):
    ApplicationFactory.create_batch(5)

    request = rf.get("/")
    request.user = core_developer

    response = ApplicationList.as_view()(request)

    assert response.status_code == 200

    assert len(response.context_data["object_list"]) == 5


def test_applicationremove_already_approved(rf, core_developer):
    application = ApplicationFactory(
        approved_at=timezone.now(), approved_by=core_developer
    )

    request = rf.post("/")
    request.user = core_developer

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = ApplicationRemove.as_view()(request, pk_hash=application.pk_hash)

    assert response.status_code == 302
    assert response.url == application.get_staff_url()

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]) == "You cannot delete an approved Application."


def test_applicationremove_already_deleted(rf, core_developer):
    application = ApplicationFactory(
        deleted_at=timezone.now(), deleted_by=UserFactory()
    )

    request = rf.post("/")
    request.user = core_developer

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = ApplicationRemove.as_view()(request, pk_hash=application.pk_hash)

    assert response.status_code == 302
    assert response.url == application.get_staff_url()

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    assert str(messages[0]) == "Application has already been deleted"


def test_applicationremove_success(rf, core_developer):
    application = ApplicationFactory()

    request = rf.post("/")
    request.user = core_developer

    response = ApplicationRemove.as_view()(request, pk_hash=application.pk_hash)

    assert response.status_code == 302
    assert response.url == reverse("staff:application-list")


def test_applicationremove_unknown_application(rf, core_developer):
    request = rf.post("/")
    request.user = core_developer

    with pytest.raises(Http404):
        ApplicationRemove.as_view()(request, pk_hash="")


def test_applicationremove_without_core_dev_role(rf):
    application = ApplicationFactory()

    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ApplicationRemove.as_view()(request, pk_hash=application.pk_hash)


def test_applicationrestore_already_deleted(rf, core_developer):
    application = ApplicationFactory(
        deleted_at=timezone.now(), deleted_by=UserFactory()
    )

    request = rf.post("/")
    request.user = core_developer

    response = ApplicationRestore.as_view()(request, pk_hash=application.pk_hash)

    assert response.status_code == 302
    assert response.url == reverse("staff:application-list")


def test_applicationrestore_success(rf, core_developer):
    application = ApplicationFactory()

    request = rf.post("/")
    request.user = core_developer

    response = ApplicationRestore.as_view()(request, pk_hash=application.pk_hash)

    assert response.status_code == 302
    assert response.url == reverse("staff:application-list")


def test_applicationrestore_unknown_application(rf, core_developer):
    request = rf.post("/")
    request.user = core_developer

    with pytest.raises(Http404):
        ApplicationRestore.as_view()(request, pk_hash="")


def test_applicationrestore_without_core_dev_role(rf):
    application = ApplicationFactory()

    request = rf.post("/")
    request.user = UserFactory()
    with pytest.raises(PermissionDenied):
        ApplicationRestore.as_view()(request, pk_hash=application.pk_hash)
