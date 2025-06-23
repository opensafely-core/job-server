import backoff
from django.conf import settings
from furl import furl

from jobserver.github import GitHubError, IssueNotFound
from jobserver.utils import strip_whitespace

from .slack import post_slack_update


def get_issue_title(workspace_name, release_request_id):
    return f"{workspace_name} {release_request_id}"


def get_github_max_retry():
    return settings.DEFAULT_MAX_GITHUB_RETRIES


@backoff.on_exception(
    backoff.expo,
    GitHubError,
    max_tries=get_github_max_retry,
    jitter=backoff.full_jitter,
)
def create_output_checking_issue(
    workspace, release_request_id, request_author, org, repo, github_api
):
    is_internal = request_author.orgs.filter(pk=settings.BENNETT_ORG_PK).exists()

    base_url = furl(settings.BASE_URL)
    requester_url = base_url / request_author.get_staff_url()
    workspace_url = base_url / workspace.get_absolute_url()

    body = f"""
    Requested by: [{request_author.fullname}]({requester_url})
    Release request ID: {release_request_id}
    GitHub repo: [{workspace.repo.name}]({workspace.repo.url})
    Workspace: [{workspace.name}]({workspace_url})

    **When you start a review please react to this message with :eyes:. When you have completed your review add a :thumbsup:.**
    """

    body = strip_whitespace(body)

    labels = {"internal" if is_internal else "external"}
    # Ensure that we don't try to add labels if they don't exist for the repo
    try:
        repo_labels = set(github_api.get_labels(org=org, repo=repo))
    except GitHubError:
        repo_labels = set()

    labels = labels & repo_labels

    data = github_api.create_issue(
        org=org,
        repo=repo,
        title=get_issue_title(workspace.name, release_request_id),
        body=body,
        labels=list(labels),
    )

    return data["html_url"]


@backoff.on_exception(
    backoff.expo,
    GitHubError,
    max_tries=get_github_max_retry,
    jitter=backoff.full_jitter,
)
def close_output_checking_issue(
    release_request_id, user, reason, org, repo, github_api
):
    data = github_api.close_issue(
        org=org,
        repo=repo,
        title_text=release_request_id,
        comment=f"Issue closed: {reason} by {user.username}",
    )

    return data["html_url"]


def notify_after_max_retries(details):
    (
        release_request_id,
        workspace_name,
        updates,
        org,
        repo,
        github_api,
        notify_slack,
        request_author,
    ) = details["args"]

    comment_url = None
    github_error_msg = str(details["exception"])

    if notify_slack:
        if github_error_msg:
            post_slack_update(
                org,
                comment_url,
                get_issue_title(workspace_name, release_request_id),
                updates,
                github_error=github_error_msg,
            )


@backoff.on_exception(
    backoff.expo,
    (IssueNotFound, GitHubError),
    max_tries=get_github_max_retry,
    jitter=backoff.full_jitter,
    on_giveup=lambda details: notify_after_max_retries(details),
)
def update_output_checking_issue(
    release_request_id,
    workspace_name,
    updates,
    org,
    repo,
    github_api,
    notify_slack,
    request_author,
):
    body = f"Release request updated:\n{updates}"

    github_error_msg = None
    try:
        data = github_api.create_issue_comment(
            org=org,
            repo=repo,
            title_text=release_request_id,
            body=body,
        )
        comment_url = data["html_url"]

    # if issue was not created in the first instance, try to create the issue again and backoff retries creating a comment
    except IssueNotFound as issue_error:
        create_output_checking_issue(
            workspace_name, release_request_id, request_author, org, repo, github_api
        )
        raise issue_error

    if notify_slack:
        post_slack_update(
            org,
            comment_url,
            get_issue_title(workspace_name, release_request_id),
            updates,
            github_error=github_error_msg,
        )
    if comment_url is not None:
        return comment_url
