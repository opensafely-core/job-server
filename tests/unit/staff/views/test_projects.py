from staff.views.projects import ProjectEdit, ProjectList

from ....factories import ProjectFactory, UserFactory


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

    response = ProjectEdit.as_view()(request, slug=project.slug)

    assert response.status_code == 403


def test_projectedit_post_success(rf, core_developer):
    project = ProjectFactory(uses_new_release_flow=False)

    request = rf.post("/", {"uses_new_release_flow": True})
    request.user = core_developer

    response = ProjectEdit.as_view()(request, slug=project.slug)

    assert response.status_code == 302
    assert response.url == project.get_staff_url()

    project.refresh_from_db()
    assert project.uses_new_release_flow


def test_projectedit_post_unauthorized(rf):
    project = ProjectFactory()

    request = rf.post("/")
    request.user = UserFactory()

    response = ProjectEdit.as_view()(request, slug=project.slug)

    assert response.status_code == 403


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

    response = ProjectList.as_view()(
        request, org_slug=project.org.slug, project_slug=project.slug
    )

    assert response.status_code == 403
