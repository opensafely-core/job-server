import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404
from django.urls import reverse

from applications.form_specs import form_specs
from applications.models import Application, ResearcherRegistration
from applications.views import (
    ApplicationList,
    ResearcherCreate,
    ResearcherDelete,
    ResearcherEdit,
    confirmation,
    get_next_url,
    page,
    sign_in,
    terms,
    validate_application_access,
)
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


def test_getnexturl_with_next_arg(rf):
    request = rf.get("/?next=/next/view/")

    output = get_next_url(request.GET)

    assert output == "/next/view/"


def test_getnexturl_without_next_arg(rf):

    request = rf.get("/")

    output = get_next_url(request.GET)

    assert output == reverse("applications:list")


def test_researchercreate_get_success(rf):
    user = UserFactory()
    application = ApplicationFactory(created_by=user)

    request = rf.get("/")
    request.user = user

    response = ResearcherCreate.as_view()(request, pk=application.pk)
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

    response = ResearcherCreate.as_view()(request, pk=application.pk)
    assert response.status_code == 302
    assert response.url == "/view/to/return/to/"


def test_researchercreate_without_permission(rf):
    application = ApplicationFactory()

    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        ResearcherCreate.as_view()(request, pk=application.pk)


def test_researchercreate_unknown_application(rf):
    request = rf.post("/")
    request.user = AnonymousUser()

    with pytest.raises(Http404):
        ResearcherCreate.as_view()(request, pk=0)


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
        request, pk=researcher.application.pk, researcher_pk=researcher.pk
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
        ResearcherDelete.as_view()(request, pk=0, researcher_pk=0)


def test_researcherdelete_unknown_researcher(rf):
    request = rf.post("/")

    with pytest.raises(Http404):
        ResearcherDelete.as_view()(request, pk=0, researcher_pk=0)

    # ResearcherEdit,


def test_researcheredit_get_success(rf):
    user = UserFactory()
    researcher = ResearcherRegistrationFactory(application__created_by=user)

    request = rf.get("/")
    request.user = user

    response = ResearcherEdit.as_view()(
        request, pk=researcher.application.pk, researcher_pk=researcher.pk
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
        request, pk=researcher.application.pk, researcher_pk=researcher.pk
    )

    assert response.status_code == 302
    assert response.url == "/view/to/return/to/"

    researcher.refresh_from_db()
    assert researcher.name == "new name"


def test_researcheredit_without_permission(rf):
    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        ResearcherEdit.as_view()(request, pk=0, researcher_pk=0)


def test_researcheredit_unknown_researcher(rf):
    request = rf.post("/")

    with pytest.raises(Http404):
        ResearcherEdit.as_view()(request, pk=0, researcher_pk=0)


def test_confirmation_success(rf):
    user = UserFactory()
    application = ApplicationFactory(created_by=user)

    request = rf.get("/")
    request.user = user

    response = confirmation(request, pk=application.pk)

    assert response.status_code == 200

    assert response.context_data["application"] == application
    for spec in form_specs:
        assert spec.title in response.rendered_content


def test_application_records_confirmation_reached(rf):
    user = UserFactory()
    application = ApplicationFactory(
        created_by=user,
    )

    request = rf.get("/")
    request.user = user

    response = confirmation(request, pk=application.pk)
    assert response.status_code == 200

    application.refresh_from_db()
    assert application.has_reached_confirmation


def test_confirmation_with_application_that_already_reached_confirmation(rf):
    user = UserFactory()
    application = ApplicationFactory(
        created_by=user,
        has_reached_confirmation=True,
    )

    request = rf.get("/")
    request.user = user

    response = confirmation(request, pk=application.pk)
    assert response.status_code == 200


def test_return_to_confirmation_once_reached(rf):
    user = UserFactory()
    application = ApplicationFactory(
        created_by=user,
        has_reached_confirmation=True,
        previous_experience_with_ehr="no",
    )

    request = rf.post("/", {"previous_experience_with_ehr": "yes"})
    request.user = user

    response = page(request, pk=application.pk, key="previous-ehr-experience")

    assert response.status_code == 302
    assert response.url == reverse(
        "applications:confirmation",
        kwargs={"pk": application.pk},
    )

    application.refresh_from_db()
    assert application.previous_experience_with_ehr == "yes"


def test_page_get_success(rf):
    user = UserFactory()
    application = ApplicationFactory(created_by=user)

    request = rf.get("/")
    request.user = user

    response = page(request, pk=application.pk, key="study-purpose")

    assert response.status_code == 200

    assert response.context_data["application"] == application


def test_page_get_404(rf):
    user = UserFactory()
    application = ApplicationFactory(created_by=user)

    request = rf.get("/")
    request.user = user

    with pytest.raises(Http404):
        page(request, pk=application.pk, key="not-a-page")


def test_page_post_final_page(rf):
    user = UserFactory()
    application = ApplicationFactory(created_by=user)

    request = rf.post("/", {"evidence_of_sharing_in_public_domain_before": "evidence"})
    request.user = user

    response = page(request, pk=application.pk, key="researcher-details")

    assert response.status_code == 302
    assert response.url == reverse(
        "applications:confirmation", kwargs={"pk": application.pk}
    )


def test_page_post_non_final_page(rf):
    user = UserFactory()
    application = ApplicationFactory(created_by=user)

    request = rf.post("/", {"previous_experience_with_ehr": "experience"})
    request.user = user

    response = page(request, pk=application.pk, key="previous-ehr-experience")

    assert response.status_code == 302
    assert response.url == reverse(
        "applications:page",
        kwargs={"pk": application.pk, "key": "software-development-experience"},
    )


def test_page_post_with_invalid_continue_state(rf):
    user = UserFactory()
    application = ApplicationFactory(
        created_by=user,
        is_study_research=False,
        is_study_service_evaluation=False,
        is_study_audit=False,
    )

    request = rf.post("/", {})
    request.user = user

    response = page(request, pk=application.pk, key="type-of-study")

    assert response.status_code == 200

    non_field_errors = response.context_data["non_field_errors"]
    assert non_field_errors == ["You must select at least one purpose"]


def test_page_post_with_invalid_prerequisite(rf):
    user = UserFactory()
    application = ApplicationFactory(created_by=user, is_study_research=False)

    request = rf.post("/", {})
    request.user = user

    response = page(request, pk=application.pk, key="references")

    assert response.status_code == 302
    assert response.url == reverse(
        "applications:page", kwargs={"pk": application.pk, "key": "cmo-priority-list"}
    )


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


def test_terms_post_success(rf):
    request = rf.post("/")
    request.user = UserFactory()

    assert Application.objects.count() == 0
    response = terms(request)

    assert response.status_code == 302

    application = Application.objects.first()
    expected_url = reverse(
        "applications:page", kwargs={"pk": application.pk, "key": "contact-details"}
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
