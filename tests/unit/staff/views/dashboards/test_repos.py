from datetime import timedelta

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from staff.views.dashboards.repos import (
    PrivateReposDashboard,
    ReposWithMultipleProjects,
)

from .....factories import (
    JobFactory,
    JobRequestFactory,
    ProjectFactory,
    RepoFactory,
    WorkspaceFactory,
)
from .....fakes import FakeGitHubAPI
from .....utils import minutes_ago


def test_privatereposdashboard_success(
    rf, django_assert_num_queries, staff_area_administrator
):
    eleven_months_ago = timezone.now() - timedelta(days=30 * 11)

    # 3 private repos
    # 1 public repo
    # 3, 2, 1 workspaces respectively for 3 private repos

    # research-repo-1
    repo1 = RepoFactory(url="https://github.com/opensafely/research-repo-1")
    rr1_workspace_1 = WorkspaceFactory(repo=repo1)
    rr1_jr_1 = JobRequestFactory(workspace=rr1_workspace_1)
    JobFactory(job_request=rr1_jr_1, started_at=minutes_ago(eleven_months_ago, 3))
    JobFactory(job_request=rr1_jr_1, started_at=minutes_ago(eleven_months_ago, 2))
    JobFactory(job_request=rr1_jr_1, started_at=minutes_ago(eleven_months_ago, 1))

    rr1_workspace_2 = WorkspaceFactory(repo=repo1)
    rr1_jr_2 = JobRequestFactory(workspace=rr1_workspace_2)
    JobFactory(job_request=rr1_jr_2, started_at=minutes_ago(eleven_months_ago, 4))
    JobFactory(job_request=rr1_jr_2, started_at=minutes_ago(eleven_months_ago, 5))

    rr1_workspace_3 = WorkspaceFactory(repo=repo1)
    rr1_jr_3 = JobRequestFactory(workspace=rr1_workspace_3)
    JobFactory(job_request=rr1_jr_3, started_at=minutes_ago(eleven_months_ago, 10))

    # research-repo-2
    repo2 = RepoFactory(url="https://github.com/opensafely/research-repo-2")
    rr2_workspace_1 = WorkspaceFactory(repo=repo2)
    rr2_jr_1 = JobRequestFactory(workspace=rr2_workspace_1)
    JobFactory(job_request=rr2_jr_1, started_at=minutes_ago(eleven_months_ago, 30))
    JobFactory(job_request=rr2_jr_1, started_at=minutes_ago(eleven_months_ago, 20))
    JobFactory(job_request=rr2_jr_1, started_at=None)

    rr2_workspace_2 = WorkspaceFactory(repo=repo2)
    rr2_jr_2 = JobRequestFactory(workspace=rr2_workspace_2)
    JobFactory(job_request=rr2_jr_2, started_at=minutes_ago(eleven_months_ago, 17))
    JobFactory(job_request=rr2_jr_2, started_at=minutes_ago(eleven_months_ago, 13))

    # research-repo-3
    rr3_workspace_1 = WorkspaceFactory(
        repo=RepoFactory(url="https://github.com/opensafely/research-repo-3")
    )
    rr3_jr_1 = JobRequestFactory(workspace=rr3_workspace_1)
    JobFactory(job_request=rr3_jr_1, started_at=minutes_ago(eleven_months_ago, 42))
    JobFactory(job_request=rr3_jr_1, started_at=minutes_ago(eleven_months_ago, 38))

    # research-repo-5
    rr5_workspace_1 = WorkspaceFactory(
        repo=RepoFactory(url="https://github.com/opensafely/research-repo-5")
    )
    rr5_jr_1 = JobRequestFactory(workspace=rr5_workspace_1)
    JobFactory(job_request=rr5_jr_1, started_at=None)

    request = rf.get("/")
    request.user = staff_area_administrator

    with django_assert_num_queries(2):
        response = PrivateReposDashboard.as_view(get_github_api=FakeGitHubAPI)(request)

    assert response.status_code == 200

    research_repo_1, research_repo_2 = response.context_data["repos"]

    assert research_repo_1["first_run"] == minutes_ago(eleven_months_ago, 10)
    assert research_repo_1["has_github_outputs"]

    assert research_repo_2["first_run"] == minutes_ago(eleven_months_ago, 30)
    assert not research_repo_2["has_github_outputs"]


def test_privatereposdashboard_unauthorized(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        PrivateReposDashboard.as_view()(request)


def test_reposwithmultipleprojects_success(
    rf, django_assert_num_queries, staff_area_administrator
):
    # research-repo-1
    repo1 = RepoFactory(url="https://github.com/opensafely/repo-1")
    WorkspaceFactory(repo=repo1)
    WorkspaceFactory(repo=repo1)

    repo2 = RepoFactory(url="https://github.com/opensafely/repo-2")
    WorkspaceFactory(repo=repo2)
    WorkspaceFactory(repo=repo2)

    repo3 = RepoFactory(url="https://github.com/opensafely/repo-3")
    WorkspaceFactory.create_batch(5, repo=repo3, project=ProjectFactory())

    request = rf.get("/")
    request.user = staff_area_administrator

    with django_assert_num_queries(2):
        response = ReposWithMultipleProjects.as_view()(request)

    assert response.status_code == 200

    assert len(response.context_data["repos"]) == 2
    assert {r["name"] for r in response.context_data["repos"]} == {
        repo1.name,
        repo2.name,
    }


def test_reposwithmultipleprojects_unauthorized(rf):
    request = rf.get("/")
    request.user = AnonymousUser()
    with pytest.raises(PermissionDenied):
        ReposWithMultipleProjects.as_view()(request)
