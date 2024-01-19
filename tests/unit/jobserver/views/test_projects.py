import pytest
import requests
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils import timezone

from jobserver.authorization import CoreDeveloper, InteractiveReporter
from jobserver.models import Project, PublishRequest, Snapshot
from jobserver.utils import set_from_list, set_from_qs
from jobserver.views.projects import (
    ProjectDetail,
    ProjectEdit,
    ProjectEventLog,
    ProjectReportList,
)

from ....factories import (
    JobFactory,
    JobRequestFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    PublishRequestFactory,
    RepoFactory,
    ReportFactory,
    SnapshotFactory,
    UserFactory,
    WorkspaceFactory,
)
from ....fakes import FakeGitHubAPI
from ....utils import minutes_ago


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


def test_projectdetail_for_interactive_button(rf, user):
    project = ProjectFactory()
    user = UserFactory(roles=[InteractiveReporter])
    ProjectMembershipFactory(project=project, user=user)

    request = rf.get("/")
    request.user = user

    response = ProjectDetail.as_view(get_github_api=FakeGitHubAPI)(
        request, project_slug=project.slug
    )

    assert response.status_code == 200
    assert "Run interactive analysis" in response.rendered_content

    user = UserFactory()
    ProjectMembershipFactory(project=project, user=user, roles=[InteractiveReporter])

    request = rf.get("/")
    request.user = user

    response = ProjectDetail.as_view(get_github_api=FakeGitHubAPI)(
        request, project_slug=project.slug
    )

    assert response.status_code == 200
    assert "Run interactive analysis" in response.rendered_content


def test_projectdetail_with_multiple_releases(rf, time_machine):
    project = ProjectFactory()

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
    request.user = UserFactory(roles=[CoreDeveloper])

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


def test_projectdetail_with_no_github(rf):
    project = ProjectFactory()
    WorkspaceFactory(
        project=project, repo=RepoFactory(url="https://github.com/owner/repo")
    )
    WorkspaceFactory(project=project, repo=RepoFactory(url="/path/on/disk/to/repo"))

    request = rf.get("/")
    request.user = UserFactory()

    class BrokenGitHubAPI:
        def get_repo_is_private(self, *args):
            raise requests.HTTPError

    response = ProjectDetail.as_view(get_github_api=BrokenGitHubAPI)(
        request, project_slug=project.slug
    )

    assert response.status_code == 200

    # check there is no public/private badge when GitHub returns an
    # unsuccessful response
    assert not response.context_data["public_repos"]
    assert response.context_data["private_repos"][0]["is_private"] is None
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
    project = ProjectFactory()

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


def test_projectedit_get_success(rf):
    project = ProjectFactory()

    user = UserFactory()
    ProjectMembershipFactory(project=project, user=user)

    request = rf.get("/")
    request.user = user

    response = ProjectEdit.as_view()(request, project_slug=project.slug)

    assert response.status_code == 200


def test_projectedit_post_success(rf):
    project = ProjectFactory(status=Project.Statuses.POSTPONED)

    user = UserFactory()
    ProjectMembershipFactory(project=project, user=user)

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


def test_projectedit_post_success_with_next(rf):
    project = ProjectFactory(status=Project.Statuses.POSTPONED)

    user = UserFactory()
    ProjectMembershipFactory(project=project, user=user)

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
def test_projectedit_without_permissions(rf, user):
    project = ProjectFactory()

    request = rf.get("/")
    # instantiate here because pytest-django disables db access by default and
    # our global fixture to re-enable it doesn't trigger early enough for the
    # parametrize call
    request.user = user()

    with pytest.raises(PermissionDenied):
        ProjectEdit.as_view()(request, project_slug=project.slug)


def test_projecteventlog_success(rf, django_assert_num_queries):
    project = ProjectFactory()
    workspace = WorkspaceFactory(project=project)

    job_requests = JobRequestFactory.create_batch(5, workspace=workspace)

    request = rf.get("/")
    request.user = UserFactory()

    with django_assert_num_queries(5):
        response = ProjectEventLog.as_view()(request, project_slug=project.slug)

    assert response.status_code == 200

    expected = set_from_list(job_requests)
    assert set_from_list(response.context_data["object_list"]) == expected


def test_projecteventlog_unknown_project(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        ProjectEventLog.as_view()(request, project_slug="")


def test_projectreportlist_success(rf, release):
    project = ProjectFactory()
    user = UserFactory()

    report1 = ReportFactory(project=project)

    report2 = ReportFactory(project=project, release_file=release.files.first())
    snapshot = SnapshotFactory()
    snapshot.files.set(release.files.all())
    PublishRequestFactory(
        report=report2,
        snapshot=snapshot,
        decision=PublishRequest.Decisions.APPROVED,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
    )

    request = rf.get("/")
    request.user = user

    response = ProjectReportList.as_view()(request, project_slug=project.slug)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {report2.pk}

    # test the page again now the user has permissions to view drafts
    ProjectMembershipFactory(project=project, user=user, roles=[InteractiveReporter])

    request = rf.get("/")
    request.user = user

    response = ProjectReportList.as_view()(request, project_slug=project.slug)

    assert response.status_code == 200
    assert set_from_qs(response.context_data["object_list"]) == {report1.pk, report2.pk}


def test_projectreportlist_unknown_project(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        ProjectReportList.as_view()(request, project_slug="")


def test_projectreportlist_with_no_reports(rf):
    project = ProjectFactory()

    request = rf.get("/")
    request.user = UserFactory()

    response = ProjectReportList.as_view()(request, project_slug=project.slug)

    assert response.status_code == 200
    assert (
        "currently no published reports for this project" in response.rendered_content
    )
