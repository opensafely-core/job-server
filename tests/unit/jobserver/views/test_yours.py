from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from jobserver.utils import set_from_qs
from jobserver.views.yours import (
    OrgList,
    ProjectList,
    WorkspaceList,
)

from ....factories import (
    OrgFactory,
    OrgMembershipFactory,
    ProjectFactory,
    UserFactory,
    WorkspaceFactory,
)


def test_orglist_success(rf):
    user = UserFactory()

    OrgFactory.create_batch(3, created_by=user)
    OrgFactory.create_batch(3)

    m1 = OrgMembershipFactory(user=user)
    m2 = OrgMembershipFactory(user=user)

    request = rf.get("/")
    request.user = user

    response = OrgList.as_view()(request)

    assert response.status_code == 200

    assert set_from_qs(response.context_data["object_list"]) == {
        m1.org.pk,
        m2.org.pk,
    }


def test_orglist_unauthorized(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    response = OrgList.as_view()(request)

    assert response.status_code == 302
    assert response.url == f"{settings.LOGIN_URL}?next={settings.LOGIN_REDIRECT_URL}"


def test_projectlist_success(rf, project_membership):
    user = UserFactory()

    ProjectFactory.create_batch(3, created_by=user)
    ProjectFactory.create_batch(3)

    m1 = project_membership(user=user)
    m2 = project_membership(user=user)

    request = rf.get("/")
    request.user = user

    response = ProjectList.as_view()(request)

    assert response.status_code == 200

    assert set_from_qs(response.context_data["object_list"]) == {
        m1.project.pk,
        m2.project.pk,
    }


def test_projectlist_unauthorized(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    response = ProjectList.as_view()(request)

    assert response.status_code == 302
    assert response.url == f"{settings.LOGIN_URL}?next={settings.LOGIN_REDIRECT_URL}"


def test_workspacelist_success(rf, project_membership):
    user = UserFactory()

    project1 = ProjectFactory(created_by=user)
    WorkspaceFactory(project=project1, created_by=user)

    project2 = ProjectFactory()
    project_membership(project=project2, user=user)
    w2 = WorkspaceFactory(project=project2)

    project3 = ProjectFactory()
    project_membership(project=project3, user=user)
    w3 = WorkspaceFactory(project=project3)

    request = rf.get("/")
    request.user = user

    response = WorkspaceList.as_view()(request)

    assert response.status_code == 200

    assert set_from_qs(response.context_data["object_list"]) == {w2.pk, w3.pk}


def test_workspacelist_unauthorized(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    response = WorkspaceList.as_view()(request)

    assert response.status_code == 302
    assert response.url == f"{settings.LOGIN_URL}?next={settings.LOGIN_REDIRECT_URL}"
