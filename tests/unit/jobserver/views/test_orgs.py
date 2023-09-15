import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from first import first

from jobserver.utils import set_from_qs
from jobserver.views.orgs import OrgDetail, OrgEventLog, OrgList

from ....factories import (
    JobRequestFactory,
    OrgFactory,
    ProjectFactory,
    UserFactory,
    WorkspaceFactory,
)


def test_orgdetail_success(rf):
    org = OrgFactory()

    request = rf.get("/")
    request.user = UserFactory()
    response = OrgDetail.as_view()(request, slug=org.slug)

    assert response.status_code == 200


def test_orgdetail_unknown_org(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        OrgDetail.as_view()(request, slug="")


def test_orgeventlog_success(rf, django_assert_num_queries):
    org = OrgFactory()
    project = ProjectFactory(orgs=[org])
    workspace = WorkspaceFactory(project=project)

    job_requests = JobRequestFactory.create_batch(5, workspace=workspace)

    request = rf.get("/")
    request.user = UserFactory()

    with django_assert_num_queries(2):
        response = OrgEventLog.as_view()(request, slug=org.slug)

    assert response.status_code == 200

    expected = {jr.pk for jr in job_requests}
    assert set_from_qs(response.context_data["object_list"]) == expected


def test_orgeventlog_unknown_org(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        OrgEventLog.as_view()(request, slug="")


@pytest.mark.parametrize(
    "user_class",
    [
        AnonymousUser,
        UserFactory,
    ],
)
def test_orglist_success(rf, user_class):
    OrgFactory.create_batch(5)

    org = OrgFactory()
    ProjectFactory.create_batch(3, orgs=[org])

    request = rf.get("/")
    request.user = user_class()

    response = OrgList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["object_list"]) == 6

    expected = first(response.context_data["object_list"], key=lambda o: o.pk == org.pk)
    assert expected and expected.project_count == 3
