from datetime import UTC, datetime

import pytest
import requests
from django.core.exceptions import PermissionDenied

from jobserver.models import Project
from staff.views.dashboards.copiloting import (
    Copiloting,
    MissingGitHubReposError,
    build_repos_by_project,
)

from .....factories import (
    JobFactory,
    JobRequestFactory,
    ProjectFactory,
    ReleaseFactory,
    ReleaseFileFactory,
    RepoFactory,
    UserFactory,
    WorkspaceFactory,
)
from .....fakes import FakeGitHubAPI


def test_build_repos_by_project_missing_github_repos():
    project = ProjectFactory()
    repo = RepoFactory()
    WorkspaceFactory(project=project, repo=repo)

    projects = Project.objects.all()

    with pytest.raises(MissingGitHubReposError):
        build_repos_by_project(projects, get_github_api=FakeGitHubAPI)


def test_build_repos_by_project_with_broken_github_api():
    project = ProjectFactory()
    repo = RepoFactory()
    WorkspaceFactory(project=project, repo=repo)

    projects = Project.objects.all()

    class BrokenGitHubAPI:
        def get_repos_with_status_and_url(self, orgs):
            # simulate the GitHub API being down
            raise requests.HTTPError()

    assert build_repos_by_project(projects, get_github_api=BrokenGitHubAPI) == {}


def test_copiloting_success(rf, core_developer):
    project = ProjectFactory()
    repo = RepoFactory(url="https://github.com/opensafely/research-repo-1")
    workspace = WorkspaceFactory(project=project, repo=repo)
    release = ReleaseFactory(workspace=workspace)
    ReleaseFileFactory.create_batch(15, release=release, workspace=workspace)

    job_request1 = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request1, started_at=datetime(2020, 7, 31, tzinfo=UTC))
    job_request2 = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request2, started_at=datetime(2021, 9, 3, tzinfo=UTC))

    request = rf.get("/")
    request.user = core_developer

    response = Copiloting.as_view(get_github_api=FakeGitHubAPI)(request)

    assert response.status_code == 200

    assert len(response.context_data["projects"]) == 1

    project = response.context_data["projects"][0]
    assert project["date_first_run"] == datetime(2020, 7, 31, 0, 0, 0, tzinfo=UTC)
    assert project["files_released_count"] == 15
    assert project["job_request_count"] == 2
    assert project["workspace_count"] == 1


def test_copiloting_unauthorized(rf):
    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(PermissionDenied):
        Copiloting.as_view(get_github_api=FakeGitHubAPI)(request)


def test_copiloting_with_broken_github_api(rf, core_developer):
    project = ProjectFactory()
    repo = RepoFactory(url="https://github.com/opensafely/research-repo-1")
    workspace = WorkspaceFactory(project=project, repo=repo)
    release = ReleaseFactory(workspace=workspace)
    ReleaseFileFactory.create_batch(15, release=release, workspace=workspace)

    job_request1 = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request1, started_at=datetime(2020, 7, 31, tzinfo=UTC))
    job_request2 = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request2, started_at=datetime(2021, 9, 3, tzinfo=UTC))

    request = rf.get("/")
    request.user = core_developer

    class BrokenGitHubAPI:
        def get_repos_with_status_and_url(self, orgs):
            # simulate the GitHub API being down
            raise requests.HTTPError()

    response = Copiloting.as_view(get_github_api=BrokenGitHubAPI)(request)

    assert response.status_code == 200

    assert len(response.context_data["projects"]) == 1

    project = response.context_data["projects"][0]
    assert project["repos"] == []
