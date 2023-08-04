import textwrap

from django.conf import settings
from django.db import transaction

from jobserver import commands
from jobserver.authorization import InteractiveReporter
from jobserver.github import _get_github_api
from jobserver.models import OrgMembership, ProjectMembership, Repo, User


def create_repo(*, name, get_github_api=_get_github_api):
    """
    Create an interactive GitHub repo

    The repo might already exist so we try to get it first, and then we ensure
    it has the correct topics set.
    """

    # local debug testsing - create a local repo rather than a github one.
    if settings.DEBUG:
        # borrow interactive_templates git wrapper
        from interactive_templates import git

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


@transaction.atomic()
def create_report(*, analysis_request, rfile, user):
    report = commands.create_report(
        rfile=rfile,
        user=user,
    )
    analysis_request.report = report
    analysis_request.save(update_fields=["report"])

    return report


def create_user(*, creator, email, name, project):
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
        org=project.org,
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

    purpose = """
    This workspace has been created for analyses requested via the OpenSAFELY Interactive point-and-click tool (opensafely.org/interactive/).
    All analyses are required to align with the approved project purpose.
    """

    workspace, _ = project.workspaces.get_or_create(
        name=project.interactive_slug,
        defaults={
            "repo": repo,
            "branch": "main",
            "created_by": creator,
            "updated_by": creator,
            "purpose": textwrap.dedent(purpose).replace("\n", " ").strip(),
        },
    )

    return workspace
