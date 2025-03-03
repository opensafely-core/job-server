from dataclasses import dataclass
from enum import Enum

from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response

from jobserver.api.authentication import get_backend_from_token
from jobserver.github import GitHubError, _get_github_api
from jobserver.models import User, Workspace

from .config import ORG_OUTPUT_CHECKING_REPOS
from .emails import (
    send_request_rejected_email,
    send_request_released_email,
    send_request_returned_email,
)
from .issues import (
    close_output_checking_issue,
    create_output_checking_issue,
    update_output_checking_issue,
)


class NotificationError(Exception): ...


class EventType(Enum):
    REQUEST_SUBMITTED = "request submitted"
    REQUEST_WITHDRAWN = "request withdrawn"
    REQUEST_APPROVED = "request approved"
    REQUEST_RELEASED = "request released"
    REQUEST_REJECTED = "request rejected"
    REQUEST_RETURNED = "request returned"
    REQUEST_RESUBMITTED = "request resubmitted"
    REQUEST_PARTIALLY_REVIEWED = "request reviewed"
    REQUEST_REVIEWED = "request reviewed"


@dataclass(frozen=True)
class AirlockEvent:
    event_type: EventType
    workspace: Workspace
    updates: list
    release_request_id: str
    request_author: User
    user: User
    org: str
    repo: str

    @classmethod
    def from_payload(cls, data):
        event_type = data.get("event_type").upper()
        try:
            event_type = EventType[event_type]
        except KeyError:
            raise NotificationError(f"Unknown event type '{event_type}'")
        updates = data.get("updates") or []
        request_author = User.objects.get(username=data.get("request_author"))
        username = data.get("user")
        if username == request_author.username:
            user = request_author
        else:
            user = User.objects.get(username=username)

        workspace = Workspace.objects.get(name=data.get("workspace"))
        org = data.get("org")
        repo = data.get("repo")
        if org is None:
            lookup = "default"
            # We check to see whether any of the project's organisations do their own
            # output checking.  If a project has multiple organisations and more than
            # one does its own output checking, we choose one arbitrarily but
            # consistently.  At time of writing (March 2025) this is a hypothetical
            # situation.
            for org in workspace.project.orgs.order_by("slug"):
                if org.slug in ORG_OUTPUT_CHECKING_REPOS:
                    lookup = org.slug
            org = ORG_OUTPUT_CHECKING_REPOS[lookup]["org"]
            repo = ORG_OUTPUT_CHECKING_REPOS[lookup]["repo"]

        workspace.project

        return cls(
            event_type=event_type,
            updates=updates,
            workspace=workspace,
            release_request_id=data.get("request"),
            request_author=request_author,
            user=user,
            org=org,
            repo=repo,
        )

    def describe_event(self):
        return self.event_type.value

    def _update_dict_to_string(self, update_dict):
        user = update_dict.get("user")
        group = update_dict.get("group")
        update = update_dict.get("update_type") or update_dict.get("update")

        update_string = update
        if group:
            update_string = f"{update_string} (filegroup {group})"
        if user:
            update_string = f"{update_string} by user {user}"
        return update_string

    def describe_updates(self):
        updates = [f"{self.describe_event()} by user {self.user.username}"]
        for update_dict in self.updates:
            updates.append(self._update_dict_to_string(update_dict))
        return updates


def create_issue(airlock_event: AirlockEvent, github_api=None):
    github_api = github_api or _get_github_api()
    try:
        create_output_checking_issue(
            airlock_event.workspace,
            airlock_event.release_request_id,
            airlock_event.request_author,
            airlock_event.org,
            airlock_event.repo,
            github_api,
        )
    except GitHubError as e:
        raise NotificationError(f"Error creating GitHub issue: {e}")


def close_issue(airlock_event: AirlockEvent, github_api=None):
    github_api = github_api or _get_github_api()
    reason = airlock_event.describe_event()
    try:
        close_output_checking_issue(
            airlock_event.release_request_id,
            airlock_event.user,
            reason,
            airlock_event.org,
            airlock_event.repo,
            github_api,
        )
    except GitHubError as e:
        raise NotificationError(f"Error closing GitHub issue: {e}")


def update_issue(airlock_event: AirlockEvent, github_api=None, notify_slack=False):
    github_api = github_api or _get_github_api()
    updates = airlock_event.describe_updates()
    try:
        update_output_checking_issue(
            airlock_event.release_request_id,
            airlock_event.workspace.name,
            updates,
            airlock_event.org,
            airlock_event.repo,
            github_api,
            notify_slack=notify_slack,
        )
    except GitHubError as e:
        raise NotificationError(f"Error creating GitHub issue comment: {e}")


def update_issue_and_slack(airlock_event, github_api=None, notify_slack=False):
    update_issue(airlock_event, github_api, notify_slack=True)


def email_author(airlock_event: AirlockEvent):
    match airlock_event.event_type:
        case EventType.REQUEST_RELEASED:
            send_request_released_email(airlock_event)
        case EventType.REQUEST_REJECTED:
            send_request_rejected_email(airlock_event)
        case EventType.REQUEST_RETURNED:
            send_request_returned_email(airlock_event)
        case _:  # pragma: no cover
            assert False


EVENT_NOTIFICATIONS = {
    EventType.REQUEST_SUBMITTED: [create_issue],
    EventType.REQUEST_WITHDRAWN: [close_issue],
    EventType.REQUEST_APPROVED: [],
    EventType.REQUEST_RELEASED: [email_author, close_issue],
    EventType.REQUEST_REJECTED: [email_author, close_issue],
    EventType.REQUEST_RETURNED: [email_author, update_issue],
    EventType.REQUEST_RESUBMITTED: [update_issue_and_slack],
    EventType.REQUEST_PARTIALLY_REVIEWED: [update_issue_and_slack],
    EventType.REQUEST_REVIEWED: [update_issue_and_slack],
}


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
def airlock_event_view(request):
    token = request.headers.get("Authorization")
    # do token authentication
    get_backend_from_token(token)

    try:
        airlock_event = AirlockEvent.from_payload(request.data)
        handle_notifications(airlock_event)
    except NotificationError as e:
        return Response({"status": "error", "message": str(e)}, status=201)
    return Response({"status": "ok"}, status=201)


def handle_notifications(airlock_event: AirlockEvent):
    for notify_fn in EVENT_NOTIFICATIONS[airlock_event.event_type]:
        notify_fn(airlock_event)
