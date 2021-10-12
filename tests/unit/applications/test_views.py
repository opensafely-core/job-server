import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404
from django.urls import reverse

from applications.form_specs import form_specs
from applications.models import Application, ResearcherRegistration, TypeOfStudyPage
from applications.views import (
    ApplicationList,
    Confirmation,
    PageRedirect,
    ResearcherCreate,
    ResearcherDelete,
    ResearcherEdit,
    get_next_url,
    notify_slack,
    page,
    sign_in,
    terms,
    validate_application_access,
)
from applications.wizard import Wizard
from jobserver.authorization import CoreDeveloper

from ...factories import ApplicationFactory, ResearcherRegistrationFactory, UserFactory


def test_applicationlist_success(rf):
    user = UserFactory()
    ApplicationFactory.create_batch(5, created_by=user)

    request = rf.get("/")
    request.user = user

    response = ApplicationList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["applications"]) == 5


def test_confirmation_get_success(rf, incomplete_application):
    request = rf.get("/")
    request.user = incomplete_application.created_by

    response = Confirmation.as_view()(request, pk_hash=incomplete_application.pk_hash)

    assert response.status_code == 200

    assert response.context_data["application"] == incomplete_application

    # check each relevant page is displayed on the confirmation page
    specs = [s for s in form_specs if s.prerequisite(incomplete_application)]
    for spec in specs:
        assert spec.title in response.rendered_content


def test_confirmation_post_invalid(rf, incomplete_application):
    request = rf.post("/")
    request.user = incomplete_application.created_by

    response = Confirmation.as_view()(request, pk_hash=incomplete_application.pk_hash)

    assert response.status_code == 200


def test_confirmation_post_success(rf, complete_application, mailoutbox, mocker):
    request = rf.post("/")
    request.user = complete_application.created_by

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    mocked_slack = mocker.patch("applications.views.slack_client", autospec=True)

    mail_count = len(mailoutbox)

    response = Confirmation.as_view()(request, pk_hash=complete_application.pk_hash)

    assert response.status_code == 302
    assert response.url == reverse("applications:list")

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    msg = "Application submitted"
    assert str(messages[0]) == msg

    assert mocked_slack.chat_postMessage.call_count == 1

    assert len(mailoutbox) == mail_count + 1


def test_getnexturl_with_next_arg(rf):
    request = rf.get("/?next=/next/view/")

    output = get_next_url(request.GET)

    assert output == "/next/view/"


def test_getnexturl_without_next_arg(rf):

    request = rf.get("/")

    output = get_next_url(request.GET)

    assert output == reverse("applications:list")


def test_notify_slack_not_called_in_debug_mode(mocker, settings):
    mocked_slack = mocker.patch("applications.views.slack_client", autospec=True)
    settings.DEBUG = True

    assert notify_slack(ApplicationFactory(), "test") is None

    assert mocked_slack.chat_postMessage.call_count == 0


def test_pageredirect_success(rf):
    request = rf.get("/")

    response = PageRedirect.as_view()(request, pk_hash="0000")

    assert response.status_code == 302

    assert response.url == reverse(
        "applications:page",
        kwargs={"pk_hash": "0000", "key": form_specs[0].key},
    )


def test_researchercreate_get_success(rf):
    user = UserFactory()
    application = ApplicationFactory(created_by=user)

    request = rf.get("/")
    request.user = user

    response = ResearcherCreate.as_view()(request, pk_hash=application.pk_hash)
    assert response.status_code == 200
    assert "is_edit" not in response.context_data


def test_researchercreate_post_success(rf):
    user = UserFactory()
    application = ApplicationFactory(created_by=user)

    data = {
        "name": "test",
        "job_title": "test",
        "email": "test",
    }
    request = rf.post("/?next=/view/to/return/to/", data)
    request.user = user

    response = ResearcherCreate.as_view()(request, pk_hash=application.pk_hash)
    assert response.status_code == 302
    assert response.url == "/view/to/return/to/"


def test_researchercreate_without_permission(rf):
    application = ApplicationFactory()

    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        ResearcherCreate.as_view()(request, pk_hash=application.pk_hash)


def test_researchercreate_unknown_application(rf):
    request = rf.post("/")
    request.user = AnonymousUser()

    with pytest.raises(Http404):
        ResearcherCreate.as_view()(request, pk_hash="0000")


def test_researcherdelete_success(rf):
    user = UserFactory()
    researcher = ResearcherRegistrationFactory(application__created_by=user)

    request = rf.post("/?next=/view/to/return/to/")
    request.user = user

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = ResearcherDelete.as_view()(
        request, pk_hash=researcher.application.pk_hash, researcher_pk=researcher.pk
    )

    assert response.status_code == 302
    assert response.url == "/view/to/return/to/"

    assert not ResearcherRegistration.objects.filter(pk=researcher.pk).exists()

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    msg = f'Successfully removed researcher "{researcher.email}" from application'
    assert str(messages[0]) == msg


def test_researcherdelete_without_permission(rf):
    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        ResearcherDelete.as_view()(request, pk_hash="0000", researcher_pk=0)


def test_researcherdelete_unknown_researcher(rf):
    request = rf.post("/")

    with pytest.raises(Http404):
        ResearcherDelete.as_view()(request, pk_hash="0000", researcher_pk=0)


def test_researcheredit_get_success(rf):
    user = UserFactory()
    researcher = ResearcherRegistrationFactory(application__created_by=user)

    request = rf.get("/")
    request.user = user

    response = ResearcherEdit.as_view()(
        request, pk_hash=researcher.application.pk_hash, researcher_pk=researcher.pk
    )

    assert response.status_code == 200
    assert response.context_data["is_edit"]


def test_researcheredit_post_success(rf):
    user = UserFactory()
    researcher = ResearcherRegistrationFactory(
        application__created_by=user,
        name="test",
    )

    data = {
        "name": "new name",
        "job_title": "job title",
        "email": "email",
    }
    request = rf.post("/?next=/view/to/return/to/", data)
    request.user = user

    response = ResearcherEdit.as_view()(
        request, pk_hash=researcher.application.pk_hash, researcher_pk=researcher.pk
    )

    assert response.status_code == 302
    assert response.url == "/view/to/return/to/"

    researcher.refresh_from_db()
    assert researcher.name == "new name"


def test_researcheredit_without_permission(rf):
    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        ResearcherEdit.as_view()(request, pk_hash="0000", researcher_pk=0)


def test_researcheredit_unknown_researcher(rf):
    request = rf.post("/")

    with pytest.raises(Http404):
        ResearcherEdit.as_view()(request, pk_hash="0000", researcher_pk=0)


def test_return_to_confirmation_once_reached(rf, complete_application):
    application = complete_application

    request = rf.post("/", {"previous_experience_with_ehr": "yes"})
    request.user = application.created_by

    response = page(request, pk_hash=application.pk_hash, key="previous-ehr-experience")

    assert response.status_code == 302
    assert response.url == reverse(
        "applications:confirmation",
        kwargs={"pk_hash": application.pk_hash},
    )

    application.refresh_from_db()
    assert application.previousehrexperiencepage.previous_experience_with_ehr == "yes"


def test_page_get_success(rf):
    user = UserFactory()
    application = ApplicationFactory(created_by=user)

    request = rf.get("/")
    request.user = user

    response = page(request, pk_hash=application.pk_hash, key="study-purpose")

    assert response.status_code == 200

    assert response.context_data["application"] == application


def test_page_get_404(rf):
    user = UserFactory()
    application = ApplicationFactory(created_by=user)

    request = rf.get("/")
    request.user = user

    with pytest.raises(Http404):
        page(request, pk_hash=application.pk_hash, key="not-a-page")


def test_page_post_final_page(rf):
    user = UserFactory()
    application = ApplicationFactory(created_by=user)

    request = rf.post("/", {"evidence_of_sharing_in_public_domain_before": "evidence"})
    request.user = user

    response = page(request, pk_hash=application.pk_hash, key="researcher-details")

    assert response.status_code == 302
    assert response.url == reverse(
        "applications:confirmation", kwargs={"pk_hash": application.pk_hash}
    )


def test_page_post_non_final_page(rf):
    user = UserFactory()
    application = ApplicationFactory(created_by=user)

    request = rf.post("/", {"previous_experience_with_ehr": "experience"})
    request.user = user

    response = page(request, pk_hash=application.pk_hash, key="previous-ehr-experience")

    assert response.status_code == 302
    assert response.url == reverse(
        "applications:page",
        kwargs={
            "pk_hash": application.pk_hash,
            "key": "software-development-experience",
        },
    )


def test_page_post_with_invalid_continue_state(rf):
    user = UserFactory()
    application = ApplicationFactory(created_by=user)
    TypeOfStudyPage.objects.create(
        application=application,
        is_study_research=False,
        is_study_service_evaluation=False,
        is_study_audit=False,
    )

    request = rf.post("/", {})
    request.user = user

    response = page(request, pk_hash=application.pk_hash, key="type-of-study")

    assert response.status_code == 200

    non_field_errors = response.context_data["non_field_errors"]
    assert non_field_errors == ["You must select at least one purpose"]


def test_page_post_with_invalid_prerequisite(rf):
    user = UserFactory()
    application = ApplicationFactory(created_by=user)
    TypeOfStudyPage.objects.create(
        application=application,
        is_study_research=False,
        is_study_service_evaluation=False,
        is_study_audit=False,
    )

    request = rf.post("/", {})
    request.user = user

    response = page(request, pk_hash=application.pk_hash, key="references")

    assert response.status_code == 302
    assert response.url == reverse(
        "applications:page",
        kwargs={"pk_hash": application.pk_hash, "key": "cmo-priority-list"},
    )


def test_approved_page_becomes_unapproved_on_edit(rf):
    user = UserFactory()
    application = ApplicationFactory(created_by=user)

    ehr_page = Wizard(application, form_specs).get_page("previous-ehr-experience")
    ehr_page.page_instance.is_approved = True
    ehr_page.page_instance.save()

    request = rf.post("/", {"previous_experience_with_ehr": "experience"})
    request.user = user

    response = page(request, pk_hash=application.pk_hash, key="previous-ehr-experience")
    assert response.status_code == 302
    ehr_page.page_instance.refresh_from_db()
    assert not ehr_page.page_instance.is_approved


def test_sign_in_with_authenticated_user(rf):
    request = rf.get("/")
    request.user = UserFactory()

    response = sign_in(request)

    assert response.status_code == 302
    assert response.url == reverse("applications:terms")


def test_sign_in_without_authenticated_user(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    response = sign_in(request)

    assert response.status_code == 200


def test_terms_get_success(rf):
    request = rf.get("/")
    request.user = UserFactory()

    response = terms(request)

    assert response.status_code == 200


def test_terms_post_success(rf, mocker):
    request = rf.post("/")
    request.user = UserFactory()

    mocker.patch("applications.views.slack_client", autospec=True)

    assert Application.objects.count() == 0
    response = terms(request)

    assert response.status_code == 302

    application = Application.objects.first()
    expected_url = reverse(
        "applications:page",
        kwargs={"pk_hash": application.pk_hash, "key": "contact-details"},
    )
    assert response.url == expected_url


def test_validate_application_access_error():
    application = ApplicationFactory()
    user = UserFactory()

    with pytest.raises(Http404):
        validate_application_access(user, application)


def test_validate_application_access_with_permission():
    application = ApplicationFactory()
    user = UserFactory(roles=[CoreDeveloper])
    assert validate_application_access(user, application) is None


def test_validate_application_access_with_owner():
    user = UserFactory()
    application = ApplicationFactory(created_by=user)
    assert validate_application_access(user, application) is None
