from django.conf import settings

from jobserver.authorization import InteractiveReporter
from jobserver.github import _get_github_api
from jobserver.models import OrgMembership, ProjectMembership, Repo, User

from .submit import git


def create_repo(*, name, get_github_api=_get_github_api):
    """
    Create an interactive GitHub repo

    The repo might already exist so we try to get it first, and then we ensure
    it has the correct topics set.
    """
    if settings.DEBUG:
        path = settings.LOCAL_GIT_REPOS / name
        path.mkdir(exist_ok=True, parents=True)

        git("init", "--bare", ".", "--initial-branch", "main", cwd=path)
        return path

    api = get_github_api()

    repo = api.get_repo("opensafely", name)

    if repo is None:
        repo = api.create_repo("opensafely", name)

    # add interactive topic to the repo if it's not already there
    topics = set(repo["topics"])
    if "interactive" not in topics:
        topics.add("interactive")
        api.set_repo_topics("opensafely", name, list(topics))

    api.add_repo_to_team("interactive", "opensafely", name)

    return repo["html_url"]


def create_user(*, creator, email, name, org, project):
    """Create an interactive user"""
    user = User.objects.create(
        fullname=name,
        email=email,
        username=email,
        created_by=creator,
        is_active=True,
    )

    OrgMembership.objects.create(
        created_by=creator,
        org=org,
        user=user,
    )

    ProjectMembership.objects.create(
        created_by=creator,
        project=project,
        user=user,
        roles=[InteractiveReporter],
    )

    return user


def create_workspace(*, creator, project, repo_url):
    """Create an interactive workspace"""
    repo, _ = Repo.objects.get_or_create(url=repo_url)

    workspace, _ = project.workspaces.get_or_create(
        name=project.interactive_slug,
        defaults={
            "repo": repo,
            "branch": "main",
            "created_by": creator,
            "purpose": "??",
        },
    )

    return workspace
