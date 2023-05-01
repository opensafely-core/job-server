from django.conf import settings
from furl import furl

from .utils import strip_whitespace


def _size_formatter(value):
    """
    Format the value, in bytes, with a size suffix

    Kilobytes (Kb) and Megabytes (Mb) will be automatically selected if the
    values is large enough.
    """
    if value < 1024:
        return f"{value}b"

    if value < 1024**2:
        value = round(value / 1024, 2)
        return f"{value}Kb"

    value = round(value / 1024**2, 2)
    return f"{value}Mb"


def create_output_checking_request(release, github_api):
    is_internal = release.created_by.orgs.filter(slug="datalab").exists()

    files = release.files.all()
    number = len(files)
    size = _size_formatter(sum(f.size for f in files))
    review_form = "" if is_internal else "[Review request form]()"

    base_url = furl(settings.BASE_URL)
    release_url = base_url / release.get_absolute_url()
    requester_url = base_url / release.created_by.get_staff_url()
    workspace_url = base_url / release.workspace.get_absolute_url()

    body = f"""
    Requested by: [{release.created_by.name}]({requester_url})
    Release: [{release.id}]({release_url})
    GitHub repo: [{release.workspace.repo.name}]({release.workspace.repo.url})
    Workspace: [{release.workspace.name}]({workspace_url})

    {number} files have been selected for review, with a total size of {size}.

    {review_form}

    **When you start a review please react to this message with :eyes:. When you have completed your review add a :thumbsup:. Once two reviews have been completed and a response has been sent to the requester, please close the issue.**
    """

    body = strip_whitespace(body)

    data = github_api.create_issue(
        org="ebmdatalab",
        repo="opensafely-output-review",
        title=release.workspace.name,
        body=body,
        labels=["internal" if is_internal else "external"],
    )

    return data["html_url"]


def create_switch_repo_to_public_request(repo, user, github_api):
    body = f"""
    The [{repo.name}]({repo.url}) repo is ready to be made public.

    This repo has been checked and approved by {user.name}.

    An owner of the `opensafely` org is required to make this change, they can do so on the [repo settings page]({repo.url}/settings).

    Once the repo is public please close this issue.
    """

    body = strip_whitespace(body)

    data = github_api.create_issue(
        org="ebmdatalab",
        repo="tech-support",
        title=f"Switch {repo.name} repo to public",
        body=body,
        labels=[],
    )

    return data["html_url"]
