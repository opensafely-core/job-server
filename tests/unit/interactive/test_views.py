from interactive.models import AnalysisRequest
from interactive.views import AnalysisRequestCreate

from ...factories import BackendFactory, ProjectFactory, WorkspaceFactory


def test_analysisrequestcreate_get_success(rf, core_developer):
    project = ProjectFactory()

    request = rf.get("/")
    request.user = core_developer

    response = AnalysisRequestCreate.as_view()(
        request, org_slug=project.org.slug, project_slug=project.slug
    )

    assert response.status_code == 200
    assert response.context_data["project"] == project


def test_analysisrequestcreate_post_success(rf, core_developer):
    BackendFactory(slug="tpp")
    project = ProjectFactory()
    WorkspaceFactory(project=project, name=f"{project.slug}-interactive")

    request = rf.post("/", {})
    request.user = core_developer

    response = AnalysisRequestCreate.as_view()(
        request, org_slug=project.org.slug, project_slug=project.slug
    )

    assert response.status_code == 302

    analysis_request = AnalysisRequest.objects.first()
    assert response.url == analysis_request.get_absolute_url()
