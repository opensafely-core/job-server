from datetime import timedelta
from urllib.parse import quote

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils import timezone

from staff.views.repos import (
    PrivateReposDashboard,
    RepoDetail,
    RepoList,
    RepoSignOff,
    ran_at,
)

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


def test_privatereposdashboard_success(rf, django_assert_num_queries, core_developer):
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
        response = PrivateReposDashboard.as_view(get_github_api=FakeGitHubAPI)(request)

    assert response.status_code == 200

    research_repo_1, research_repo_2 = response.context_data["repos"]

    assert research_repo_1["first_run"] == minutes_ago(eleven_months_ago, 10)
    assert research_repo_1["has_github_outputs"]
    assert research_repo_1["workspace"] == rr1_workspace_3

    assert research_repo_2["first_run"] == minutes_ago(eleven_months_ago, 30)
    assert not research_repo_2["has_github_outputs"]
    assert research_repo_2["workspace"] == rr2_workspace_1


def test_privatereposdashboard_unauthorized(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        PrivateReposDashboard.as_view()(request)


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


def test_repodetail_sign_off_disabled_when_already_internally_signed_off(
    rf, core_developer
):
    repo = RepoFactory(
        researcher_signed_off_at=timezone.now(),
        researcher_signed_off_by=UserFactory(),
        internal_signed_off_at=timezone.now(),
        internal_signed_off_by=UserFactory(),
    )
    workspace = WorkspaceFactory(repo=repo)
    job_request = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request)

    request = rf.get("/")
    request.user = core_developer

    response = RepoDetail.as_view(get_github_api=FakeGitHubAPI)(
        request, repo_url=quote(repo.url)
    )

    assert response.status_code == 200
    assert response.context_data["disabled"] == {
        "already_signed_off": True,
        "no_permission": False,
        "not_ready": False,
    }
    assert (
        "This repo has already been internally signed off" in response.rendered_content
    )


def test_repodetail_sign_off_disabled_when_repo_has_github_outputs_but_user_is_missing_role(
    rf, core_developer
):
    repo = RepoFactory(
        has_github_outputs=True,
        researcher_signed_off_at=timezone.now(),
        researcher_signed_off_by=UserFactory(),
    )
    workspace = WorkspaceFactory(repo=repo)
    job_request = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request)

    request = rf.get("/")
    request.user = core_developer

    response = RepoDetail.as_view(get_github_api=FakeGitHubAPI)(
        request, repo_url=quote(repo.url)
    )

    assert response.status_code == 200
    assert response.context_data["disabled"] == {
        "already_signed_off": False,
        "no_permission": True,
        "not_ready": False,
    }
    assert (
        "The SignOffRepoWithOutputs role is required to sign off repos with outputs on GitHub"
        in response.rendered_content
    )


def test_repodetail_sign_off_disabled_when_repo_missing_researcher_sign_off(
    rf, core_developer
):
    repo = RepoFactory()
    workspace = WorkspaceFactory(repo=repo)
    job_request = JobRequestFactory(workspace=workspace)
    JobFactory(job_request=job_request)

    request = rf.get("/")
    request.user = core_developer

    response = RepoDetail.as_view(get_github_api=FakeGitHubAPI)(
        request, repo_url=quote(repo.url)
    )

    assert response.status_code == 200
    assert response.context_data["disabled"] == {
        "already_signed_off": False,
        "no_permission": False,
        "not_ready": True,
    }
    assert "A researcher has not yet signed this repo off" in response.rendered_content


def test_repodetail_unauthorized(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        RepoDetail.as_view(get_github_api=FakeGitHubAPI)(request, repo_url="test")


def test_repolist_filter_by_org(rf, core_developer):
    repo = RepoFactory()
    RepoFactory.create_batch(2)
    WorkspaceFactory(repo=repo)

    request = rf.get(f"/?org={repo.workspaces.first().project.org.slug}")
    request.user = core_developer

    response = RepoList.as_view()(request)

    assert len(response.context_data["object_list"]) == 1


def test_repolist_filter_by_outputs(rf, core_developer):
    RepoFactory(has_github_outputs=False)
    RepoFactory.create_batch(2, has_github_outputs=True)

    request = rf.get("/?has_outputs=yes")
    request.user = core_developer

    response = RepoList.as_view()(request)

    assert len(response.context_data["object_list"]) == 2


def test_repolist_find_by_name(rf, core_developer):
    repo1 = RepoFactory(url="age-test-distribution")
    repo2 = RepoFactory(url="ghickman-testing")
    RepoFactory(url="sro-measures")

    request = rf.get("/?q=test")
    request.user = core_developer

    response = RepoList.as_view()(request)

    assert response.status_code == 200
    assert set(response.context_data["object_list"]) == {repo1, repo2}


def test_repolist_success(rf, core_developer):
    RepoFactory.create_batch(5)

    request = rf.get("/")
    request.user = core_developer

    response = RepoList.as_view()(request)

    assert response.status_code == 200
    assert len(response.context_data["object_list"])


def test_repolist_unauthorized(rf):
    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        RepoList.as_view()(request)


def test_reposignoff_success(rf, core_developer):
    repo = RepoFactory()

    request = rf.post("/")
    request.user = core_developer

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = RepoSignOff.as_view(get_github_api=FakeGitHubAPI)(
        request, repo_url=repo.url
    )

    assert response.status_code == 302
    assert response.url == repo.get_staff_url()

    repo.refresh_from_db()
    assert repo.internal_signed_off_at
    assert repo.internal_signed_off_by

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    assert (
        str(messages[0])
        == 'A <a href="http://example.com">ticket has been created</a> for tech-support, they have been notified in #tech-support-channel'
    )


def test_reposignoff_unauthorized(rf):
    request = rf.post("/")
    request.user = AnonymousUser()

    with pytest.raises(PermissionDenied):
        RepoSignOff.as_view(get_github_api=FakeGitHubAPI)(request)


def test_reposignoff_unknown_repo(rf, core_developer):
    request = rf.post("/")
    request.user = core_developer

    with pytest.raises(Http404):
        RepoSignOff.as_view(get_github_api=FakeGitHubAPI)(request, repo_url="test")


def test_reposignoff_without_sign_off_role(rf, core_developer):
    repo = RepoFactory(has_github_outputs=True)

    request = rf.post("/")
    request.user = core_developer

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = RepoSignOff.as_view(get_github_api=FakeGitHubAPI)(
        request, repo_url=repo.url
    )

    assert response.status_code == 302
    assert response.url == repo.get_staff_url()

    repo.refresh_from_db()
    assert repo.internal_signed_off_at is None
    assert repo.internal_signed_off_by is None

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    msg = "The SignOffRepoWithOutputs role is required to sign off repos with outputs hosted on GitHub"
    assert str(messages[0]) == msg
