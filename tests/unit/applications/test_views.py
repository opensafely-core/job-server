import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.urls import reverse

from applications.form_specs import form_specs
from applications.models import Application
from applications.views import (
    confirmation,
    page,
    sign_in,
    terms,
    validate_application_access,
)
from jobserver.authorization import CoreDeveloper

from ...factories import ApplicationFactory, UserFactory


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


def test_confirmation_success(rf):
    user = UserFactory()
    application = ApplicationFactory(created_by=user)

    request = rf.get("/")
    request.user = user

    response = confirmation(request, pk=application.pk)

    assert response.status_code == 200

    assert response.context_data["application"] == application
    for spec in form_specs:
        assert spec["title"] in response.rendered_content


def test_page_get_success(rf):
    user = UserFactory()
    application = ApplicationFactory(created_by=user)

    request = rf.get("/")
    request.user = user

    response = page(request, pk=application.pk, page_num=3)

    assert response.status_code == 200

    assert response.context_data["application"] == application


def test_page_post_final_page(rf):
    user = UserFactory()
    application = ApplicationFactory(created_by=user)

    request = rf.post("/", {"evidence_of_sharing_in_public_domain_before": "evidence"})
    request.user = user

    response = page(request, pk=application.pk, page_num=15)

    assert response.status_code == 302
    assert response.url == reverse(
        "applications:confirmation", kwargs={"pk": application.pk}
    )


def test_page_post_non_final_page(rf):
    user = UserFactory()
    application = ApplicationFactory(created_by=user)

    request = rf.post("/", {"previous_experience_with_ehr": "experience"})
    request.user = user

    response = page(request, pk=application.pk, page_num=13)

    assert response.status_code == 302
    assert response.url == reverse(
        "applications:page", kwargs={"pk": application.pk, "page_num": 14}
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

    response = page(request, pk=application.pk, page_num=6)

    assert response.status_code == 200

    form = response.context_data["form"]
    assert not form.is_valid(), form.errors
    assert form.non_field_errors() == ["You must select at least one purpose"]


def test_page_post_with_invalid_prerequisite(rf):
    user = UserFactory()
    application = ApplicationFactory(created_by=user, is_study_research=False)

    request = rf.post("/", {})
    request.user = user

    response = page(request, pk=application.pk, page_num=7)

    assert response.status_code == 302
    assert response.url == reverse(
        "applications:page", kwargs={"pk": application.pk, "page_num": 9}
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
        "applications:page", kwargs={"pk": application.pk, "page_num": 1}
    )
    assert response.url == expected_url
