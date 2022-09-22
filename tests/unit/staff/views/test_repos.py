from datetime import timedelta
from urllib.parse import quote

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from staff.views.repos import RepoDetail, RepoList, ran_at

from ....factories import (
    JobFactory,
    JobRequestFactory,
    RepoFactory,
    UserFactory,
    WorkspaceFactory,
)
from ....fakes import FakeGitHubAPI
from ....utils import minutes_ago


def test_ran_at():
    created = minutes_ago(timezone.now(), 1)
    started = timezone.now()

    assert ran_at(JobFactory(created_at=created, started_at=None)) == created
    assert ran_at(JobFactory(created_at=created, started_at=started)) == started


def test_repodetail_success(rf, core_developer):
    repo = RepoFactory(url="https://github.com/opensafely-testing/github-api-testing")

    workspace1 = WorkspaceFactory(repo=repo)
    job_request1 = JobRequestFactory(workspace=workspace1)
    JobFactory(job_request=job_request1, created_at=timezone.now())

    workspace2 = WorkspaceFactory(repo=repo)
    job_request2 = JobRequestFactory(workspace=workspace2)
    JobFactory(job_request=job_request2, created_at=timezone.now())

    user = UserFactory()
    workspace3 = WorkspaceFactory(repo=repo, created_by=user)
    job_request3 = JobRequestFactory(workspace=workspace3, created_by=user)
    JobFactory(job_request=job_request3, created_at=timezone.now())

    workspace4 = WorkspaceFactory(repo=repo)
    job_request4 = JobRequestFactory(workspace=workspace4)
    JobFactory(job_request=job_request4, created_at=timezone.now())

    request = rf.get("/")
    request.user = core_developer

    response = RepoDetail.as_view(get_github_api=FakeGitHubAPI)(
        request, repo_url=quote(repo.url)
    )

    assert response.status_code == 200
    assert len(response.context_data["workspaces"]) == 4


def test_repodetail_unauthorized(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        RepoDetail.as_view(get_github_api=FakeGitHubAPI)(request, repo_url="test")


def test_repolist_success(rf, django_assert_num_queries, core_developer):
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
    request.user = core_developer

    with django_assert_num_queries(1):
        response = RepoList.as_view(get_github_api=FakeGitHubAPI)(request)

    assert response.status_code == 200

    research_repo_1, research_repo_2 = response.context_data["repos"]

    assert research_repo_1["first_run"] == minutes_ago(eleven_months_ago, 10)
    assert research_repo_1["has_releases"]
    assert research_repo_1["workspace"] == rr1_workspace_3

    assert research_repo_2["first_run"] == minutes_ago(eleven_months_ago, 30)
    assert not research_repo_2["has_releases"]
    assert research_repo_2["workspace"] == rr2_workspace_1


def test_repolist_unauthorized(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        RepoList.as_view(get_github_api=FakeGitHubAPI)(request)
