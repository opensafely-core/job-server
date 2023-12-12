from urllib.parse import quote

import pytest
import requests
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404
from django.utils import timezone

from jobserver.views.repos import RepoHandler, SignOffRepo

from ....factories import (
    OrgFactory,
    ProjectFactory,
    ProjectMembershipFactory,
    RepoFactory,
    UserFactory,
    WorkspaceFactory,
)
from ....fakes import FakeGitHubAPI


def test_repohandler_with_broken_repo_url(rf):
    # set up an org with the GitHub org we use in the URL below so it passes
    # the allowlist validation
    OrgFactory(github_orgs=["opensafely-testing"])

    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(Http404):
        RepoHandler.as_view()(request, repo_url="https://github.com/opensafely-testing")


@pytest.mark.parametrize("url", ["http://example.com", "http://github.com/not-us"])
def test_repohandler_with_disallowed_url(rf, url):
    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(Http404):
        RepoHandler.as_view()(request, repo_url=url)


def test_repohandler_repo_with_multiple_projects(rf):
    repo = RepoFactory(url="https://github.com/opensafely/foo")

    project1 = ProjectFactory()
    WorkspaceFactory(project=project1, repo=repo)

    project2 = ProjectFactory()
    WorkspaceFactory(project=project2, repo=repo)

    request = rf.get("/")
    request.user = AnonymousUser()

    response = RepoHandler.as_view()(request, repo_url=repo.quoted_url)

    assert response.status_code == 200


def test_repohandler_repo_with_one_project(rf):
    project = ProjectFactory()
    repo = RepoFactory(url="https://github.com/opensafely/foo")
    WorkspaceFactory(project=project, repo=repo)

    request = rf.get("/")
    request.user = AnonymousUser()

    response = RepoHandler.as_view()(request, repo_url=repo.quoted_url)

    assert response.status_code == 302
    assert response.url == project.get_absolute_url()


def test_repohandler_with_unknown_repo(rf):
    # set up an org with the GitHub org we use in the URL below so it passes
    # the allowlist validation
    OrgFactory(github_orgs=["opensafely-testing"])

    request = rf.get("/")
    request.user = AnonymousUser()

    repo_url = quote("https://github.com/opensafely-testing/unknown-repo", safe="")

    response = RepoHandler.as_view()(request, repo_url=repo_url)

    assert response.status_code == 200


def test_signoffrepo_get_success_with_multiple_projects(rf):
    user = UserFactory()
    project1 = ProjectFactory()
    project2 = ProjectFactory()
    repo = RepoFactory(url="http://example.com/owner/name")

    ProjectMembershipFactory(project=project1, user=user)

    workspaces1 = WorkspaceFactory.create_batch(5, project=project1, repo=repo)
    workspaces2 = WorkspaceFactory.create_batch(5, project=project2, repo=repo)
    workspaces = workspaces1 + workspaces2
    WorkspaceFactory.create_batch(5, project=project1)

    request = rf.get("/")
    request.user = user

    response = SignOffRepo.as_view(get_github_api=FakeGitHubAPI)(
        request, repo_url=repo.quoted_url
    )

    assert response.status_code == 200

    expected = {w["name"] for w in response.context_data["workspaces"]}
    assert {w.name for w in workspaces} == expected

    assert response.context_data["project_url"] == repo.get_handler_url()
    assert response.context_data["repo"]["is_private"]
    assert response.context_data["repo"]["name"] == "name"
    assert response.context_data["repo"]["status"] == "private"
    assert response.context_data["repo"]["url"] == repo.url


def test_signoffrepo_get_success_with_one_project(rf):
    user = UserFactory()
    project = ProjectFactory()
    repo = RepoFactory(url="http://example.com/owner/name")

    ProjectMembershipFactory(project=project, user=user)

    workspaces = WorkspaceFactory.create_batch(5, project=project, repo=repo)
    WorkspaceFactory.create_batch(5, project=project)

    request = rf.get("/")
    request.user = user

    response = SignOffRepo.as_view(get_github_api=FakeGitHubAPI)(
        request, repo_url=repo.quoted_url
    )

    assert response.status_code == 200

    expected = {w["name"] for w in response.context_data["workspaces"]}
    assert {w.name for w in workspaces} == expected

    url = quote(repo.get_sign_off_url(), safe="")
    project_url = project.get_edit_url() + f"?next={url}"

    assert response.context_data["project_url"] == project_url
    assert response.context_data["repo"]["is_private"]
    assert response.context_data["repo"]["name"] == "name"
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
        request, repo_url=repo.quoted_url
    )

    assert response.status_code == 200

    expected = {w["name"] for w in response.context_data["workspaces"]}
    assert {w.name for w in workspaces} == expected

    assert response.context_data["repo"]["is_private"] is None
    assert response.context_data["repo"]["name"] == "name"
    assert response.context_data["repo"]["status"] == "public"
    assert response.context_data["repo"]["url"] == repo.url


def test_signoffrepo_member_with_no_workspaces(rf):
    user = UserFactory()
    project = ProjectFactory()
    repo = RepoFactory()
    WorkspaceFactory.create_batch(5)

    ProjectMembershipFactory(project=project, user=user)

    request = rf.get("/")
    request.user = user

    with pytest.raises(Http404):
        SignOffRepo.as_view(get_github_api=FakeGitHubAPI)(
            request, repo_url=repo.quoted_url
        )


def test_signoffrepo_sign_offs_disabled(rf):
    repo = RepoFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        SignOffRepo.as_view(get_github_api=FakeGitHubAPI)(
            request, repo_url=repo.quoted_url
        )


def test_signoffrepo_not_a_project_member(rf):
    repo = RepoFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        SignOffRepo.as_view(get_github_api=FakeGitHubAPI)(
            request, repo_url=repo.quoted_url
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
        request, repo_url=repo.quoted_url
    )

    assert response.status_code == 200

    repo.refresh_from_db()
    assert not repo.researcher_signed_off_at


def test_signoffrepo_post_all_workspaces_signed_off_and_no_name_with_github_outputs(
    rf, mailoutbox, slack_messages
):
    user = UserFactory()
    project = ProjectFactory()
    ProjectMembershipFactory(project=project, user=user)

    repo = RepoFactory(
        researcher_signed_off_at=None,
        researcher_signed_off_by=None,
        has_github_outputs=True,
    )
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
        request, repo_url=repo.quoted_url
    )

    assert response.status_code == 302
    assert response.url == "/"

    repo.refresh_from_db()
    assert repo.researcher_signed_off_at
    assert repo.researcher_signed_off_by

    assert len(mailoutbox) == 2
    assert len(slack_messages) == 0


def test_signoffrepo_post_all_workspaces_signed_off_and_no_name_without_github_outputs(
    rf, mailoutbox, slack_messages
):
    user = UserFactory()
    copilot = UserFactory()
    project = ProjectFactory(copilot=copilot)
    ProjectMembershipFactory(project=project, user=user)

    repo = RepoFactory(
        researcher_signed_off_at=None,
        researcher_signed_off_by=None,
        has_github_outputs=False,
    )
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
        request, repo_url=repo.quoted_url
    )

    assert response.status_code == 302
    assert response.url == "/"

    repo.refresh_from_db()
    assert repo.researcher_signed_off_at
    assert repo.researcher_signed_off_by

    assert len(mailoutbox) == 1
    assert len(slack_messages) == 1
    msg, channel = slack_messages[0]
    assert copilot.name in msg
    assert channel == "co-pilot-support"


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
        request, repo_url=repo.quoted_url
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
        request, repo_url=repo.quoted_url
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
        request, repo_url=repo.quoted_url
    )

    assert response.status_code == 200

    # check we have a message for the user
    messages = list(messages)
    assert len(messages) == 1
    assert (
        str(messages[0]) == "Please sign off all workspaces before signing off the repo"
    )
