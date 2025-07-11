from enum import Enum

from django.conf import settings
from furl import furl

from jobserver.github import GitHubError
from jobserver.utils import strip_whitespace

from .slack import post_slack_update


class IssueStatusLabel(Enum):
    PENDING_REVIEW = "Pending review"
    UNDER_REVIEW = "Under review"
    WITH_REQUESTER = "With requester"


def get_issue_title(workspace_name, release_request_id):
    return f"{workspace_name} {release_request_id}"


def ensure_issue_status_labels(org, repo, github_api, repo_labels):
    status_labels = {x.value for x in IssueStatusLabel}
    unknown_labels = status_labels - repo_labels
    for label in unknown_labels:
        try:
            github_api.create_label(org=org, repo=repo, label_name=label)
            repo_labels.add(label)
        except GitHubError:
            ...
    return repo_labels


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

    labels = {
        "internal" if is_internal else "external",
        IssueStatusLabel.PENDING_REVIEW.value,
    }
    try:
        repo_labels = set(github_api.get_labels(org=org, repo=repo))
    except GitHubError:
        repo_labels = set()

    # Ensure all issue status labels exist on the repo
    repo_labels = ensure_issue_status_labels(org, repo, github_api, repo_labels)
    # Ensure that we don't try to add labels if they don't exist for the repo
    labels = labels & repo_labels

    data = github_api.create_issue(
        org=org,
        repo=repo,
        title=get_issue_title(workspace.name, release_request_id),
        body=body,
        labels=list(labels),
    )

    return data["html_url"]


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


def update_output_checking_issue(
    release_request_id, workspace_name, updates, org, repo, github_api, notify_slack
):
    updates_string = "\n".join([f"- {update}" for update in updates])
    body = f"Release request updated:\n{updates_string}"

    github_error_msg = None
    try:
        data = github_api.create_issue_comment(
            org=org,
            repo=repo,
            title_text=release_request_id,
            body=body,
        )
        comment_url = data["html_url"]
    except GitHubError as error:
        comment_url = None
        github_error_msg = str(error)
        raise error
    finally:
        if notify_slack:
            post_slack_update(
                org,
                comment_url,
                get_issue_title(workspace_name, release_request_id),
                updates_string,
                github_error=github_error_msg,
            )
        if comment_url is not None:
            return comment_url
