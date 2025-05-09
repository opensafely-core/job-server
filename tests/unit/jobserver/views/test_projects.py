import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils import timezone

from jobserver.authorization import StaffAreaAdministrator, permissions
from jobserver.models import Project, PublishRequest, Snapshot
from jobserver.utils import set_from_list, set_from_qs
from jobserver.views.projects import (
    ProjectDetail,
    ProjectEdit,
    ProjectEventLog,
)
from tests.fakes import FakeGitHubAPI, FakeGitHubAPIWithErrors
from tests.utils import minutes_ago

from ....factories import (
    JobFactory,
    JobRequestFactory,
    OrgFactory,
    ProjectFactory,
    PublishRequestFactory,
    RepoFactory,
    SnapshotFactory,
    UserFactory,
    WorkspaceFactory,
)


@pytest.mark.parametrize("user", [UserFactory, AnonymousUser])
def test_projectdetail_success(rf, user):
    project = ProjectFactory()
    repo = RepoFactory(url="https://github.com/opensafely/some-research")
    workspace = WorkspaceFactory(project=project, repo=repo)
    job_request = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request, started_at=timezone.now())

    request = rf.get("/")

    # instantiate here because pytest-django disables db access by default and
    # our global fixture to re-enable it doesn't trigger early enough for the
    # parametrize call
    request.user = user()

    response = ProjectDetail.as_view(get_github_api=FakeGitHubAPI)(
        request, project_slug=project.slug
    )

    assert response.status_code == 200

    assert not response.context_data["public_repos"]
    assert response.context_data["private_repos"] == [
        {
            "name": "some-research",
            "url": "https://github.com/opensafely/some-research",
            "is_private": True,
        }
    ]

    # check the staff-only edit link doesn't show for normal users
    assert "Edit" not in response.context_data


def test_projectdetail_with_multiple_releases(rf, freezer):
    project = ProjectFactory(org=OrgFactory())

    now = timezone.now()

    workspace1 = WorkspaceFactory(project=project)
    snapshot1 = SnapshotFactory(workspace=workspace1)
    PublishRequestFactory(
        snapshot=snapshot1,
        decision=PublishRequest.Decisions.APPROVED,
        decision_at=minutes_ago(now, 2),
        decision_by=UserFactory(),
    )
    snapshot2 = SnapshotFactory(workspace=workspace1)
    PublishRequestFactory(
        snapshot=snapshot2,
        decision=PublishRequest.Decisions.APPROVED,
        decision_at=minutes_ago(now, 3),
        decision_by=UserFactory(),
    )

    workspace2 = WorkspaceFactory(project=project)
    snapshot3 = SnapshotFactory(workspace=workspace2)
    PublishRequestFactory(
        snapshot=snapshot3,
        decision=PublishRequest.Decisions.APPROVED,
        decision_at=minutes_ago(now, 1),
        decision_by=UserFactory(),
    )

    # unpublished
    workspace3 = WorkspaceFactory(project=project)
    snapshot4 = SnapshotFactory(workspace=workspace3)
    PublishRequestFactory(snapshot=snapshot4)

    workspace4 = WorkspaceFactory(project=project)
    snapshot5 = SnapshotFactory(
        workspace=workspace4,
    )
    PublishRequestFactory(
        snapshot=snapshot5,
        decision=PublishRequest.Decisions.APPROVED,
        decision_at=minutes_ago(now, 4),
        decision_by=UserFactory(),
    )

    request = rf.get("/")
    # FIXME: remove this role when releases is deployed to all users
    request.user = UserFactory(roles=[StaffAreaAdministrator])

    response = ProjectDetail.as_view(get_github_api=FakeGitHubAPI)(
        request, project_slug=project.slug
    )

    assert response.status_code == 200

    assert "Outputs" in response.rendered_content

    # check the ordering of responses, should be latest first
    assert len(response.context_data["outputs"]) == 3
    output_pks = list(response.context_data["outputs"].values_list("pk", flat=True))
    expected_pks = [snapshot3.pk, snapshot1.pk, snapshot5.pk]
    assert output_pks == expected_pks

    # check unpublished or published-but-older snapshots are not in the
    # snapshots picked to display for outputs
    snapshots = set_from_qs(Snapshot.objects.all())
    assert snapshot2 not in snapshots
    assert snapshot4 not in snapshots


def test_projectdetail_with_github_error(rf):
    project = ProjectFactory(org=OrgFactory())
    WorkspaceFactory(
        project=project, repo=RepoFactory(url="https://github.com/owner/repo")
    )
    WorkspaceFactory(project=project, repo=RepoFactory(url="/path/on/disk/to/repo"))

    request = rf.get("/")
    request.user = UserFactory()

    response = ProjectDetail.as_view(get_github_api=FakeGitHubAPIWithErrors)(
        request, project_slug=project.slug
    )

    assert response.status_code == 200

    # check there is no public/private badge when GitHub returns an
    # unsuccessful response
    assert not response.context_data["public_repos"]
    assert response.context_data["private_repos"][0]["is_private"] is None
    assert "Public" not in response.rendered_content


def test_projectdetail_with_timed_out_github(rf):
    project = ProjectFactory(org=OrgFactory())
    WorkspaceFactory(
        project=project, repo=RepoFactory(url="https://github.com/owner/repo")
    )
    WorkspaceFactory(project=project, repo=RepoFactory(url="/path/on/disk/to/repo"))

    request = rf.get("/")
    request.user = UserFactory()

    class BrokenGitHubAPI:
        def get_repo_is_private(self, *args):
            raise TimeoutError

    response = ProjectDetail.as_view(get_github_api=BrokenGitHubAPI)(
        request, project_slug=project.slug
    )

    assert response.status_code == 200

    # check there is no public/private badge when GitHub returns an
    # unsuccessful response
    assert not response.context_data["public_repos"]
    assert response.context_data["private_repos"][0] == {
        "name": "GitHub API Unavailable",
        "is_private": None,
        "url": "",
    }
    assert "Public" not in response.rendered_content


def test_projectdetail_with_no_jobs(rf):
    project = ProjectFactory()

    request = rf.get("/")
    request.user = UserFactory()

    response = ProjectDetail.as_view(get_github_api=FakeGitHubAPI)(
        request, project_slug=project.slug
    )

    assert response.status_code == 200

    assert response.context_data["first_job_ran_at"] is None


def test_projectdetail_with_no_releases(rf):
    project = ProjectFactory(org=OrgFactory())

    request = rf.get("/")
    request.user = UserFactory()

    response = ProjectDetail.as_view(get_github_api=FakeGitHubAPI)(
        request, project_slug=project.slug
    )

    assert response.status_code == 200

    assert len(response.context_data["outputs"]) == 0
    assert "Outputs" not in response.rendered_content


def test_projectdetail_unknown_project(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        ProjectDetail.as_view()(request, project_slug="test")


def test_projectedit_get_success(rf, project_membership, role_factory):
    project = ProjectFactory()

    user = UserFactory()
    project_membership(
        project=project,
        user=user,
        roles=[role_factory(permission=permissions.project_manage)],
    )

    request = rf.get("/")
    request.user = user

    response = ProjectEdit.as_view()(request, project_slug=project.slug)

    assert response.status_code == 200


def test_projectedit_post_success(rf, project_membership, role_factory):
    project = ProjectFactory(status=Project.Statuses.POSTPONED)

    user = UserFactory()
    project_membership(
        project=project,
        user=user,
        roles=[role_factory(permission=permissions.project_manage)],
    )

    data = {
        "status": Project.Statuses.ONGOING,
        "status_description": "test",
    }
    request = rf.post("/", data=data)
    request.user = user

    response = ProjectEdit.as_view()(request, project_slug=project.slug)

    assert response.status_code == 302
    assert response.url == project.get_absolute_url()

    project.refresh_from_db()
    assert project.status == Project.Statuses.ONGOING
    assert project.status_description == "test"


def test_projectedit_post_success_with_next(rf, project_membership, role_factory):
    project = ProjectFactory(status=Project.Statuses.POSTPONED)

    user = UserFactory()
    project_membership(
        project=project,
        user=user,
        roles=[role_factory(permission=permissions.project_manage)],
    )

    data = {
        "status": Project.Statuses.ONGOING,
        "status_description": "test",
    }
    request = rf.post("/?next=/foo", data=data)
    request.user = user

    response = ProjectEdit.as_view()(request, project_slug=project.slug)

    assert response.status_code == 302
    assert response.url == "/foo"

    project.refresh_from_db()
    assert project.status == Project.Statuses.ONGOING
    assert project.status_description == "test"


def test_projectedit_unknown_project(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        ProjectEdit.as_view()(request, project_slug="test")


@pytest.mark.parametrize("user", [UserFactory, AnonymousUser])
def test_projectedit_user_is_not_member(rf, user):
    project = ProjectFactory()

    request = rf.get("/")
    # instantiate here because pytest-django disables db access by default and
    # our global fixture to re-enable it doesn't trigger early enough for the
    # parametrize call
    request.user = user()

    with pytest.raises(PermissionDenied):
        ProjectEdit.as_view()(request, project_slug=project.slug)


def test_projectedit_user_has_global_project_manage(
    rf, project_membership, role_factory
):
    project = ProjectFactory()
    user = UserFactory(roles=[role_factory(permission=permissions.project_manage)])
    project_membership(project=project, user=user)
    request = rf.get("/")
    request.user = user

    response = ProjectEdit.as_view()(request, project_slug=project.slug)

    assert response.status_code == 200


def test_projectedit_member_does_not_have_project_manage(rf, project_membership):
    project = ProjectFactory()
    user = UserFactory()
    project_membership(project=project, user=user)
    request = rf.get("/")
    request.user = user

    with pytest.raises(PermissionDenied):
        ProjectEdit.as_view()(request, project_slug=project.slug)


def test_projecteventlog_success(rf):
    project = ProjectFactory()
    workspace = WorkspaceFactory(project=project)

    job_requests = JobRequestFactory.create_batch(5, workspace=workspace)

    request = rf.get("/")
    request.user = UserFactory()

    response = ProjectEventLog.as_view()(request, project_slug=project.slug)

    assert response.status_code == 200

    expected = set_from_list(job_requests)
    assert set_from_list(response.context_data["object_list"]) == expected


def test_projecteventlog_num_queries(rf, django_assert_num_queries):
    project = ProjectFactory()
    JobRequestFactory.create_batch(5, workspace=WorkspaceFactory(project=project))

    request = rf.get("/")
    request.user = UserFactory()

    with django_assert_num_queries(2):
        response = ProjectEventLog.as_view()(request, project_slug=project.slug)
        assert response.status_code == 200

    with django_assert_num_queries(7):
        response.render()


def test_projecteventlog_unknown_project(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        ProjectEventLog.as_view()(request, project_slug="")
