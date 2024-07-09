import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from applications.models import Application
from jobserver.utils import set_from_list
from staff.views.applications import (
    ApplicationApprove,
    ApplicationDetail,
    ApplicationEdit,
    ApplicationList,
    ApplicationRemove,
    ApplicationRestore,
)

from ....factories import ApplicationFactory, OrgFactory, ProjectFactory, UserFactory


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
    ProjectFactory(number=7)  # check default is set via Form.initial

    request = rf.get("/")
    request.user = core_developer

    response = ApplicationApprove.as_view()(
        request, pk_hash=complete_application.pk_hash
    )

    assert response.status_code == 200
    assert response.context_data["application"] == complete_application
    assert response.context_data["form"]["org"].initial is None
    assert response.context_data["form"]["project_number"].initial == 8


def test_applicationapprove_num_queries(
    rf, django_assert_num_queries, core_developer, complete_application
):
    request = rf.get("/")
    request.user = core_developer

    with django_assert_num_queries(4):
        response = ApplicationApprove.as_view()(
            request, pk_hash=complete_application.pk_hash
        )
        assert response.status_code == 200

    with django_assert_num_queries(1):
        response.render()


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


def test_applicationapprove_post_success(
    rf, django_assert_num_queries, core_developer, complete_application
):
    assert complete_application.approved_at is None
    assert complete_application.approved_by is None

    org = OrgFactory()

    data = {
        "project_name": complete_application.studyinformationpage.study_name,
        "project_number": "42",
        "org": str(org.pk),
    }
    request = rf.post("/", data)
    request.user = core_developer

    with django_assert_num_queries(15):
        response = ApplicationApprove.as_view()(
            request, pk_hash=complete_application.pk_hash
        )

    assert response.status_code == 302, response.context_data["form"].errors

    complete_application.refresh_from_db()

    assert complete_application.approved_at
    assert complete_application.approved_by == core_developer
    assert complete_application.project
    assert complete_application.project.created_by == core_developer
    assert complete_application.project.updated_by == core_developer
    assert complete_application.project.number == 42


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


def test_applicationdetail_num_queries(
    rf, django_assert_max_num_queries, core_developer, complete_application
):
    request = rf.get("/")
    request.user = core_developer

    with django_assert_max_num_queries(19):
        response = ApplicationDetail.as_view()(
            request, pk_hash=complete_application.pk_hash
        )
        assert response.status_code == 200

    with django_assert_max_num_queries(36):
        response.render()


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
    django_assert_max_num_queries,
    core_developer,
    complete_application,
    time_machine,
):
    now = timezone.now()
    time_machine.move_to(now, tick=False)

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

    with django_assert_max_num_queries(34):
        response = ApplicationDetail.as_view()(request, pk_hash=application.pk_hash)

    assert response.status_code == 302

    application.refresh_from_db()

    assert application.contactdetailspage.notes == "could do better"
    assert application.contactdetailspage.is_approved is False
    assert application.studyinformationpage.notes == "couldn't do better"
    assert application.studyinformationpage.is_approved is True

    assert application.contactdetailspage.last_reviewed_at == now
    assert application.contactdetailspage.reviewed_by == request.user
    assert application.studyinformationpage.last_reviewed_at == now
    assert application.studyinformationpage.reviewed_by == request.user


def test_applicationdetail_post_with_incomplete_application(
    rf,
    core_developer,
    incomplete_application,
    time_machine,
):
    now = timezone.now()
    time_machine.move_to(now, tick=False)

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

    assert application.contactdetailspage.last_reviewed_at == now
    assert application.contactdetailspage.reviewed_by == request.user
    assert application.studyinformationpage.last_reviewed_at == now
    assert application.studyinformationpage.reviewed_by == request.user

    # Check that a page instance has not been created
    with pytest.raises(ObjectDoesNotExist):
        application.researcherdetailspage


def test_applicationedit_get_success(rf, django_assert_num_queries, core_developer):
    application = ApplicationFactory()

    request = rf.get("/")
    request.user = core_developer

    with django_assert_num_queries(1):
        response = ApplicationEdit.as_view()(request, pk_hash=application.pk_hash)

    assert response.status_code == 200


def test_applicationedit_post_success(rf, django_assert_num_queries, core_developer):
    application = ApplicationFactory(status=Application.Statuses.ONGOING)

    data = {
        "status": Application.Statuses.COMPLETED,
        "status_comment": "Completed and ready for review",
    }
    request = rf.post("/", data)
    request.user = core_developer

    with django_assert_num_queries(2):
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


def test_applicationlist_filter_by_status(rf, core_developer):
    ApplicationFactory(status=Application.Statuses.APPROVED_FULLY)

    request = rf.get("/?status=approved_fully")
    request.user = core_developer

    response = ApplicationList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


def test_applicationlist_filter_by_user(rf, core_developer):
    ApplicationFactory.create_batch(5)
    application = ApplicationFactory()

    request = rf.get(f"/?user={application.created_by.username}")
    request.user = core_developer

    response = ApplicationList.as_view()(request)

    assert list(response.context_data["object_list"]) == [application]


def test_applicationlist_search(rf, core_developer):
    app1 = ApplicationFactory(created_by=UserFactory(fullname="ben g"))
    app2 = ApplicationFactory(created_by=UserFactory(username="ben"))
    ApplicationFactory(created_by=UserFactory(username="seb"))

    request = rf.get("/?q=ben")
    request.user = core_developer

    response = ApplicationList.as_view()(request)

    assert response.status_code == 200
    assert set_from_list(response.context_data["object_list"]) == {app1.pk, app2.pk}


def test_applicationlist_success(rf, django_assert_num_queries, core_developer):
    ApplicationFactory.create_batch(5)

    request = rf.get("/")
    request.user = core_developer

    with django_assert_num_queries(2):
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


def test_applicationremove_success(rf, django_assert_num_queries, core_developer):
    application = ApplicationFactory()

    request = rf.post("/")
    request.user = core_developer

    with django_assert_num_queries(2):
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


def test_applicationrestore_success(rf, django_assert_num_queries, core_developer):
    application = ApplicationFactory()

    request = rf.post("/")
    request.user = core_developer

    with django_assert_num_queries(1):
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
