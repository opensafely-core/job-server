from urllib.parse import quote

import pytest
import requests
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404
from django.utils import timezone

from jobserver.views.repos import SignOffRepo

from ....factories import (
    ProjectFactory,
    ProjectMembershipFactory,
    RepoFactory,
    UserFactory,
    WorkspaceFactory,
)
from ....fakes import FakeGitHubAPI


def test_signoffrepo_get_success(rf):
    user = UserFactory()
    project = ProjectFactory()
    repo = RepoFactory(url="http://example.com/owner/name")

    ProjectMembershipFactory(project=project, user=user)

    workspaces = WorkspaceFactory.create_batch(5, project=project, repo=repo)
    WorkspaceFactory.create_batch(5, project=project)

    request = rf.get("/")
    request.user = user

    response = SignOffRepo.as_view(get_github_api=FakeGitHubAPI)(
        request, repo_url=quote(repo.url)
    )

    assert response.status_code == 200

    expected = {w["name"] for w in response.context_data["workspaces"]}
    assert {w.name for w in workspaces} == expected

    assert response.context_data["repo"]["is_private"]
    assert response.context_data["repo"]["name"] == "owner/name"
    assert response.context_data["repo"]["status"] == "private"
    assert response.context_data["repo"]["url"] == repo.url


def test_signoffrepo_get_success_with_broken_github(rf):
    user = UserFactory()
    project = ProjectFactory()
    repo = RepoFactory(url="http://example.com/owner/name")

    ProjectMembershipFactory(project=project, user=user)

    workspaces = WorkspaceFactory.create_batch(5, project=project, repo=repo)
    WorkspaceFactory.create_batch(5, project=project)

    request = rf.get("/")
    request.user = user

    class BrokenGitHubAPI:
        def get_branch(self, owner, repo, branch):
            return {}

        def get_branches(self, owner, repo):
            return []

        def get_repo_is_private(self, owner, repo):
            raise requests.HTTPError()

    response = SignOffRepo.as_view(get_github_api=BrokenGitHubAPI)(
        request, repo_url=quote(repo.url)
    )

    assert response.status_code == 200

    expected = {w["name"] for w in response.context_data["workspaces"]}
    assert {w.name for w in workspaces} == expected

    assert response.context_data["repo"]["is_private"] is None
    assert response.context_data["repo"]["name"] == "owner/name"
    assert response.context_data["repo"]["status"] == "public"
    assert response.context_data["repo"]["url"] == repo.url


def test_signoffrepo_member_with_no_workspaces(rf):
    user = UserFactory()
    project = ProjectFactory()

    ProjectMembershipFactory(project=project, user=user)

    WorkspaceFactory.create_batch(5)

    request = rf.get("/")
    request.user = user

    with pytest.raises(Http404):
        SignOffRepo.as_view(get_github_api=FakeGitHubAPI())(request, repo_url="test")


def test_signoffrepo_not_a_project_member(rf):
    workspace = WorkspaceFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        SignOffRepo.as_view(get_github_api=FakeGitHubAPI)(
            request, repo_url=workspace.repo.url
        )


def test_signoffrepo_post_all_workspaces_signed_off_and_name(rf):
    now = timezone.now()

    user = UserFactory()

    project = ProjectFactory()
    ProjectMembershipFactory(project=project, user=user)

    repo = RepoFactory()
    WorkspaceFactory(project=project, repo=repo, signed_off_at=now, signed_off_by=user)
    WorkspaceFactory(
        project=project,
        repo=repo,
        signed_off_at=now,
        signed_off_by=user,
        name="test",
    )

    request = rf.post("/", {"name": "test"})
    request.user = user

    response = SignOffRepo.as_view(get_github_api=FakeGitHubAPI)(
        request, repo_url=repo.url
    )

    assert response.status_code == 200

    repo.refresh_from_db()
    assert not repo.researcher_signed_off_at


def test_signoffrepo_post_all_workspaces_signed_off_and_no_name(rf):
    user = UserFactory()
    project = ProjectFactory()
    ProjectMembershipFactory(project=project, user=user)

    repo = RepoFactory(researcher_signed_off_at=None, researcher_signed_off_by=None)
    WorkspaceFactory.create_batch(
        3,
        project=project,
        repo=repo,
        signed_off_at=timezone.now(),
        signed_off_by=user,
    )

    request = rf.post("/")
    request.user = user

    response = SignOffRepo.as_view(get_github_api=FakeGitHubAPI)(
        request, repo_url=repo.url
    )

    assert response.status_code == 302
    assert response.url == "/"

    repo.refresh_from_db()
    assert repo.researcher_signed_off_at
    assert repo.researcher_signed_off_by


def test_signoffrepo_post_no_signed_off_workspaces_and_no_name(rf):
    user = UserFactory()
    project = ProjectFactory()
    ProjectMembershipFactory(project=project, user=user)

    repo = RepoFactory()
    WorkspaceFactory(project=project, repo=repo)
    WorkspaceFactory(project=project, repo=repo)

    request = rf.post("/")
    request.user = user

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = SignOffRepo.as_view(get_github_api=FakeGitHubAPI)(
        request, repo_url=repo.url
    )
    assert response.status_code == 200

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    assert (
        str(messages[0]) == "Please sign off all workspaces before signing off the repo"
    )


def test_signoffrepo_post_partially_signed_off_workspaces_and_name(rf):
    user = UserFactory()
    project = ProjectFactory()
    repo = RepoFactory()
    workspace = WorkspaceFactory(project=project, repo=repo)

    ProjectMembershipFactory(project=project, user=user)

    request = rf.post("/", {"name": workspace.name})
    request.user = user

    response = SignOffRepo.as_view(get_github_api=FakeGitHubAPI)(
        request, repo_url=repo.url
    )

    assert response.status_code == 302
    assert response.url == repo.get_sign_off_url()

    workspace.refresh_from_db()
    assert workspace.signed_off_at


def test_signoffrepo_post_partially_signed_off_workspaces_and_no_name(rf):
    user = UserFactory()
    project = ProjectFactory()
    repo = RepoFactory(url="https://github.com/opensafely-testing/github-api-testing")
    WorkspaceFactory(project=project, repo=repo)

    ProjectMembershipFactory(project=project, user=user)

    request = rf.post("/")
    request.user = user

    # set up messages framework
    request.session = "session"
    messages = FallbackStorage(request)
    request._messages = messages

    response = SignOffRepo.as_view(get_github_api=FakeGitHubAPI)(
        request, repo_url=repo.url
    )

    assert response.status_code == 200

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    assert (
        str(messages[0]) == "Please sign off all workspaces before signing off the repo"
    )
