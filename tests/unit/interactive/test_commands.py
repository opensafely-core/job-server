import pytest
from django.conf import settings

from interactive.commands import create_repo, create_user, create_workspace
from jobserver.authorization import InteractiveReporter
from jobserver.models import AuditableEvent
from jobserver.utils import set_from_qs

from ...factories import (
    OrgFactory,
    ProjectFactory,
    RepoFactory,
    UserFactory,
    WorkspaceFactory,
)
from ...fakes import FakeGitHubAPI


@pytest.mark.parametrize(
    "debug,expected",
    [
        (True, settings.BASE_DIR / "repos" / "testing"),
        (False, "http://example.com"),
    ],
    ids=["debug-on", "debug-off"],
)
def test_create_repo_with_existing_repo(monkeypatch, debug, expected):
    monkeypatch.setattr(settings, "DEBUG", debug)

    repo_url = create_repo(name="testing", get_github_api=FakeGitHubAPI)

    assert repo_url == expected


def test_createrepo_with_existing_repo_and_exsting_interactive_topic():
    class MissingGitHubRepoAPI(FakeGitHubAPI):
        def get_repo(self, org, repo):
            return {
                "html_url": "http://example.com",
                "topics": ["interactive"],
            }

    repo_url = create_repo(name="new", get_github_api=MissingGitHubRepoAPI)

    assert repo_url == "http://example.com"


def test_createrepo_with_missing_repo():
    class MissingGitHubRepoAPI(FakeGitHubAPI):
        def get_repo(self, org, repo):
            return None

    repo_url = create_repo(name="new", get_github_api=MissingGitHubRepoAPI)

    assert repo_url == "http://example.com"


def test_create_user():
    creator = UserFactory()
    org = OrgFactory()
    project = ProjectFactory(orgs=[org])

    user = create_user(
        creator=creator,
        email="test@example.com",
        name="Testing McTesterson",
        project=project,
    )

    assert user.created_by == creator
    assert user.name == "Testing McTesterson"
    assert user.email == "test@example.com"
    assert set_from_qs(user.orgs.all()) == set_from_qs(project.orgs.all())
    assert set_from_qs(user.projects.all()) == {project.pk}

    assert user.project_memberships.first().roles == [InteractiveReporter]

    assert AuditableEvent.objects.count() == 2

    # light touch sense check that we're creating the right type of event, the
    # tests for members.add will check all the relevant parts of the event
    first, second = AuditableEvent.objects.all()
    assert first.type == AuditableEvent.Type.PROJECT_MEMBER_ADDED
    assert second.type == AuditableEvent.Type.PROJECT_MEMBER_UPDATED_ROLES


def test_create_workspace_with_existing_objects():
    creator = UserFactory()
    project = ProjectFactory()
    repo = RepoFactory(url="http://example.com/interactive/repo")
    existing_workspace = WorkspaceFactory(
        project=project, repo=repo, name=project.interactive_slug
    )

    workspace = create_workspace(
        creator=creator,
        project=project,
        repo_url="http://example.com/interactive/repo",
    )

    assert workspace == existing_workspace


def test_create_workspace_without_existing_objects():
    creator = UserFactory()
    project = ProjectFactory()

    workspace = create_workspace(
        creator=creator,
        project=project,
        repo_url="http://example.com/interactive/repo",
    )

    assert workspace.branch == "main"
    assert workspace.created_by == creator
    assert workspace.name == project.interactive_slug
    assert workspace.purpose
    assert workspace.repo.url == "http://example.com/interactive/repo"
