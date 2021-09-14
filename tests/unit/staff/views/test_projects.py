import pytest
from django.core.exceptions import PermissionDenied

from jobserver.utils import set_from_qs
from staff.views.projects import ProjectDetail, ProjectEdit, ProjectList

from ....factories import ProjectFactory, UserFactory


def test_projectdetail_success(rf, core_developer):
    project = ProjectFactory()

    request = rf.get("/")
    request.user = core_developer

    response = ProjectDetail.as_view()(request, slug=project.slug)

    assert response.status_code == 200

    expected = set_from_qs(project.workspaces.all())
    output = set_from_qs(response.context_data["workspaces"])
    assert output == expected


def test_projectedit_get_success(rf, core_developer):
    project = ProjectFactory()

    request = rf.get("/")
    request.user = core_developer

    response = ProjectEdit.as_view()(request, slug=project.slug)

    assert response.status_code == 200


def test_projectedit_get_unauthorized(rf):
    project = ProjectFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ProjectEdit.as_view()(request, slug=project.slug)


def test_projectedit_post_success(rf, core_developer):
    project = ProjectFactory(uses_new_release_flow=False)

    data = {
        "name": "new-name",
        "uses_new_release_flow": True,
    }
    request = rf.post("/", data)
    request.user = core_developer

    response = ProjectEdit.as_view()(request, slug=project.slug)

    assert response.status_code == 302, response.context_data["form"].errors
    assert response.url == project.get_staff_url()

    project.refresh_from_db()
    assert project.name == "new-name"
    assert project.uses_new_release_flow


def test_projectedit_post_unauthorized(rf):
    project = ProjectFactory()

    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ProjectEdit.as_view()(request, slug=project.slug)


def test_projectlist_filter_by_org(rf, core_developer):
    project = ProjectFactory()
    ProjectFactory.create_batch(2)

    request = rf.get(f"/?org={project.org.slug}")
    request.user = core_developer

    response = ProjectList.as_view()(request)

    assert len(response.context_data["project_list"]) == 1


def test_projectlist_find_by_username(rf, core_developer):
    ProjectFactory(name="ben")
    ProjectFactory(name="benjamin")
    ProjectFactory(name="seb")

    request = rf.get("/?q=ben")
    request.user = core_developer

    response = ProjectList.as_view()(request)

    assert response.status_code == 200

    assert len(response.context_data["project_list"]) == 2


def test_projectlist_success(rf, core_developer):
    ProjectFactory.create_batch(5)

    request = rf.get("/")
    request.user = core_developer

    response = ProjectList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["project_list"])


def test_projectlist_unauthorized(rf):
    project = ProjectFactory()

    request = rf.post("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        ProjectList.as_view()(
            request,
            org_slug=project.org.slug,
            project_slug=project.slug,
        )
