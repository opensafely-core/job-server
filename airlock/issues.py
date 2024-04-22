from django.conf import settings
from furl import furl

from jobserver.utils import strip_whitespace


def get_issue_title(workspace_name, release_request_id):
    return f"{workspace_name} {release_request_id}"


def create_output_checking_issue(
    workspace, release_request_id, request_author, github_api
):
    is_internal = request_author.orgs.filter(pk=settings.BENNETT_ORG_PK).exists()

    base_url = furl(settings.BASE_URL)
    requester_url = base_url / request_author.get_staff_url()
    workspace_url = base_url / workspace.get_absolute_url()

    body = f"""
    Requested by: [{request_author.name}]({requester_url})
    Release request ID: {release_request_id}
    GitHub repo: [{workspace.repo.name}]({workspace.repo.url})
    Workspace: [{workspace.name}]({workspace_url})

    **When you start a review please react to this message with :eyes:. When you have completed your review add a :thumbsup:.**
    """

    body = strip_whitespace(body)

    data = github_api.create_issue(
        org="ebmdatalab",
        repo="opensafely-output-review",
        title=get_issue_title(workspace.name, release_request_id),
        body=body,
        labels=["internal" if is_internal else "external"],
    )

    return data["html_url"]
