import pytest
from django.core.exceptions import PermissionDenied

from interactive.models import AnalysisRequest
from interactive.views import AnalysisRequestCreate, AnalysisRequestDetail
from jobserver.authorization import InteractiveReporter

from ...factories import (
    AnalysisRequestFactory,
    BackendFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    UserFactory,
    WorkspaceFactory,
)


def test_analysisrequestcreate_get_success(rf):
    project = ProjectFactory()
    user = UserFactory()

    ProjectMembershipFactory(project=project, user=user, roles=[InteractiveReporter])

    request = rf.get("/")
    request.user = user

    response = AnalysisRequestCreate.as_view()(
        request, org_slug=project.org.slug, project_slug=project.slug
    )

    assert response.status_code == 200
    assert response.context_data["project"] == project


def test_analysisrequestcreate_post_success(rf):
    BackendFactory(slug="tpp")
    project = ProjectFactory()
    user = UserFactory()
    WorkspaceFactory(project=project, name=f"{project.slug}-interactive")

    ProjectMembershipFactory(project=project, user=user, roles=[InteractiveReporter])

    request = rf.post("/", {})
    request.user = user

    response = AnalysisRequestCreate.as_view()(
        request, org_slug=project.org.slug, project_slug=project.slug
    )

    assert response.status_code == 302

    analysis_request = AnalysisRequest.objects.first()
    assert response.url == analysis_request.get_absolute_url()


def test_analysisrequestcreate_unauthorized(rf):
    project = ProjectFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        AnalysisRequestCreate.as_view()(
            request, org_slug=project.org.slug, project_slug=project.slug
        )


def test_analysisrequestdetail_success(rf):
    project = ProjectFactory()
    user = UserFactory()
    analysis_request = AnalysisRequestFactory(project=project, created_by=user)

    ProjectMembershipFactory(project=project, user=user, roles=[InteractiveReporter])

    request = rf.get("/")
    request.user = user

    response = AnalysisRequestDetail.as_view()(
        request,
        org_slug=analysis_request.project.org.slug,
        project_slug=analysis_request.project.slug,
        pk=analysis_request.pk,
    )

    assert response.status_code == 200


def test_analysisrequestdetail_with_global_interactivereporter(rf):
    analysis_request = AnalysisRequestFactory()

    request = rf.get("/")
    request.user = UserFactory(roles=[InteractiveReporter])

    response = AnalysisRequestDetail.as_view()(
        request,
        org_slug=analysis_request.project.org.slug,
        project_slug=analysis_request.project.slug,
        pk=analysis_request.pk,
    )

    assert response.status_code == 200


def test_analysisrequestdetail_with_interactivereporter_on_another_project(rf):
    analysis_request = AnalysisRequestFactory()

    user = UserFactory()
    ProjectMembershipFactory(user=user, roles=[InteractiveReporter])

    request = rf.get("/")
    request.user = user

    with pytest.raises(PermissionDenied):
        AnalysisRequestDetail.as_view()(
            request,
            org_slug=analysis_request.project.org.slug,
            project_slug=analysis_request.project.slug,
            pk=analysis_request.pk,
        )


def test_analysisrequestdetail_with_no_interactivereporter_role(rf):
    analysis_request = AnalysisRequestFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        AnalysisRequestDetail.as_view()(
            request,
            org_slug=analysis_request.project.org.slug,
            project_slug=analysis_request.project.slug,
            pk=analysis_request.pk,
        )
