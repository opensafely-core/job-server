import pytest
from django.http import Http404

from jobserver.models import Project
from jobserver.views.projects import (
    ProjectCreate,
    ProjectDetail,
    ProjectDisconnectWorkspace,
    ProjectSettings,
)

from ...factories import (
    OrgFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    WorkspaceFactory,
)


MEANINGLESS_URL = "/"


@pytest.mark.django_db
def test_projectcreate_get_success(rf, superuser):
    org = OrgFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser
    response = ProjectCreate.as_view()(request, org_slug=org.slug)

    assert response.status_code == 200


@pytest.mark.django_db
def test_projectcreate_get_unknown_org(rf, superuser):
    request = rf.get(MEANINGLESS_URL)
    request.user = superuser

    with pytest.raises(Http404):
        ProjectCreate.as_view()(request, org_slug="")


@pytest.mark.django_db
def test_projectcreate_post_invalid_data(rf, superuser):
    org = OrgFactory()

    data = {
        "name": "",
        "project_lead": "",
        "email": "",
        "researcher-TOTAL_FORMS": "0",
        "researcher-INITIAL_FORMS": "0",
        "researcher-MIN_NUM": "0",
        "researcher-MAX_NUM": "1000",
    }

    request = rf.post(MEANINGLESS_URL, data)
    request.user = superuser
    response = ProjectCreate.as_view()(request, org_slug=org.slug)

    assert response.status_code == 200
    assert Project.objects.count() == 0


@pytest.mark.django_db
def test_projectcreate_post_success(rf, superuser):
    org = OrgFactory()

    data = {
        "name": "A Brand New Project",
        "project_lead": "My Name",
        "email": "name@example.com",
        "researcher-TOTAL_FORMS": "1",
        "researcher-INITIAL_FORMS": "0",
        "researcher-MIN_NUM": "0",
        "researcher-MAX_NUM": "1000",
        "researcher-0-name": "Test",
        "researcher-0-passed_researcher_training_at": "2021-01-01",
        "researcher-0-is_ons_accredited_researcher": "on",
    }

    request = rf.post(MEANINGLESS_URL, data)
    request.user = superuser
    response = ProjectCreate.as_view()(request, org_slug=org.slug)

    assert response.status_code == 302

    projects = Project.objects.all()
    assert len(projects) == 1

    project = projects.first()
    assert project.name == "A Brand New Project"
    assert project.project_lead == "My Name"
    assert project.email == "name@example.com"
    assert project.org == org
    assert response.url == project.get_absolute_url()


@pytest.mark.django_db
def test_projectcreate_post_unknown_org(rf, superuser):
    request = rf.post(MEANINGLESS_URL)
    request.user = superuser

    with pytest.raises(Http404):
        ProjectCreate.as_view()(request, org_slug="")


@pytest.mark.django_db
def test_projectdetail_success(rf, superuser):
    org = OrgFactory()
    project = ProjectFactory(org=org)

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser
    response = ProjectDetail.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_projectdetail_unknown_org(rf, superuser):
    project = ProjectFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser

    with pytest.raises(Http404):
        ProjectDetail.as_view()(request, org_slug="test", project_slug=project.slug)


@pytest.mark.django_db
def test_projectdetail_unknown_project(rf, superuser):
    org = OrgFactory()

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser

    with pytest.raises(Http404):
        ProjectDetail.as_view()(request, org_slug=org.slug, project_slug="test")


@pytest.mark.django_db
def test_projectdisconnect_missing_workspace_id(rf, superuser):
    org = OrgFactory()
    project = ProjectFactory(org=org)

    request = rf.post(MEANINGLESS_URL)
    request.user = superuser
    response = ProjectDisconnectWorkspace.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 302
    assert response.url == project.get_absolute_url()


@pytest.mark.django_db
def test_projectdisconnect_success(rf, superuser):
    org = OrgFactory()
    project = ProjectFactory(org=org)
    workspace = WorkspaceFactory(project=project)

    request = rf.post(MEANINGLESS_URL, {"id": workspace.pk})
    request.user = superuser
    response = ProjectDisconnectWorkspace.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 302
    assert response.url == project.get_absolute_url()


@pytest.mark.django_db
def test_projectdisconnect_unknown_project(rf, superuser):
    org = OrgFactory()

    request = rf.post(MEANINGLESS_URL)
    request.user = superuser

    with pytest.raises(Http404):
        ProjectDisconnectWorkspace.as_view()(
            request, org_slug=org.slug, project_slug=""
        )


@pytest.mark.django_db
def test_projectsettings_success(rf, superuser):
    org = OrgFactory()
    project = ProjectFactory(org=org)

    ProjectMembershipFactory(project=project)

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser

    response = ProjectSettings.as_view()(
        request, org_slug=org.slug, project_slug=project.slug
    )

    assert response.status_code == 200

    assert len(response.context_data["members"]) == 1
    assert response.context_data["project"] == project


@pytest.mark.django_db
def test_projectsettings_unknown_project(rf, superuser):

    request = rf.get(MEANINGLESS_URL)
    request.user = superuser

    with pytest.raises(Http404):
        ProjectSettings.as_view()(request, org_slug="", project_slug="")
