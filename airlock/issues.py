from enum import Enum

import stamina
from django.conf import settings
from furl import furl

from jobserver.github import GitHubError, IssueNotFound
from jobserver.utils import strip_whitespace

from .slack import post_slack_update


class IssueStatusLabel(Enum):
    PENDING_REVIEW = "Pending review"
    UNDER_REVIEW = "Under review"
    WITH_REQUESTER = "With requester"


def get_issue_title(workspace_name, release_request_id):
    return f"{workspace_name} {release_request_id}"


def ensure_issue_status_labels(org, repo, github_api):
    try:
        repo_labels = set(github_api.get_labels(org=org, repo=repo))
    except GitHubError:
        repo_labels = set()

    status_labels = {x.value for x in IssueStatusLabel}
    unknown_labels = status_labels - repo_labels
    for label in unknown_labels:
        try:
            github_api.create_label(org=org, repo=repo, label_name=label)
            repo_labels.add(label)
        except GitHubError:
            ...
    return repo_labels


def get_github_max_retry():
    return settings.DEFAULT_MAX_GITHUB_RETRIES


@stamina.retry(on=GitHubError, attempts=get_github_max_retry(), wait_jitter=1.0)
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

    # Ensure all issue status labels exist on the repo
    repo_labels = ensure_issue_status_labels(org, repo, github_api)
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


def get_non_status_issue_labels(org, repo, issue_number, github_api):
    # get existing labels excluding any status labels
    try:
        labels = set(
            github_api.get_issue_labels(org=org, repo=repo, issue_number=issue_number)
        )
    except GitHubError:
        labels = set()
    status_labels = {x.value for x in IssueStatusLabel}
    labels = labels - status_labels
    return labels


@stamina.retry(on=GitHubError, attempts=get_github_max_retry(), wait_jitter=1.0)
def close_output_checking_issue(
    release_request_id, user, reason, org, repo, github_api
):
    title_text = release_request_id

    try:
        issue_number = github_api.get_issue_number_from_title(
            org=org, repo=repo, title_text=title_text
        )
    except GitHubError:
        # If we get an error here, ignore it and let create_issue_comment retry
        issue_number = None

    # remove any non-status labels for this closed issue
    labels = get_non_status_issue_labels(org, repo, issue_number, github_api)

    data = github_api.close_issue(
        org=org,
        repo=repo,
        title_text=title_text,
        comment=f"Issue closed: {reason} by {user.username}",
        issue_number=issue_number,
        labels=list(labels),
    )

    return data["html_url"]


@stamina.retry(
    on=(IssueNotFound, GitHubError), attempts=get_github_max_retry(), wait_jitter=1.0
)
def _update_output_checking_issue(
    release_request_id,
    workspace_name,
    updates,
    org,
    repo,
    github_api,
    notify_slack,
    request_author,
    label,
):
    body = f"Release request updated:\n{updates}"

    github_error_msg = None

    title_text = release_request_id
    try:
        issue_number = github_api.get_issue_number_from_title(
            org=org, repo=repo, title_text=title_text
        )
    except GitHubError:
        # If we get an error here, ignore it and let create_issue_comment retry
        issue_number = None

    ensure_issue_status_labels(org, repo, github_api)
    # get existing non-status labels and add the current one
    labels = get_non_status_issue_labels(org, repo, issue_number, github_api)
    if label is not None:
        labels.add(label.value)

    try:
        data = github_api.create_issue_comment(
            org=org,
            repo=repo,
            title_text=title_text,
            body=body,
            issue_number=issue_number,
            labels=list(labels),
        )
        comment_url = data["html_url"]

    # if issue was not created in the first instance, try to create the issue again and stamina retries creating a comment
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
            github_error_msg,
        )

    return comment_url


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
    try:
        return _update_output_checking_issue(
            release_request_id,
            workspace_name,
            updates,
            org,
            repo,
            github_api,
            notify_slack,
            request_author,
        )

    except GitHubError as error:
        comment_url = None
        github_error_msg = str(error)

        post_slack_update(
            org,
            comment_url,
            get_issue_title(workspace_name, release_request_id),
            updates,
            github_error_msg,
        )
        raise error
