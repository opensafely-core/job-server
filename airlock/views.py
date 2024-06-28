from dataclasses import dataclass
from enum import Enum

from requests.exceptions import HTTPError
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response

from jobserver.api.authentication import get_backend_from_token
from jobserver.github import _get_github_api
from jobserver.models import User, Workspace

from .config import ORG_OUTPUT_CHECKING_REPOS
from .emails import (
    send_request_rejected_email,
    send_request_released_email,
    send_request_returned_email,
    send_request_updated_email,
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
    REQUEST_UPDATED = "request updated"
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
            lookup = (
                workspace.project.slug
                if workspace.project.slug in ORG_OUTPUT_CHECKING_REPOS
                else "default"
            )
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

    def describe_updates(self):
        if self.event_type in [
            EventType.REQUEST_RESUBMITTED,
            EventType.REQUEST_RETURNED,
            EventType.REQUEST_PARTIALLY_REVIEWED,
            EventType.REQUEST_REVIEWED,
        ]:
            return [f"{self.describe_event()} by user {self.user.username}"]

        return [
            f"{update['update_type']} (filegroup {update['group']}) by user {update['user']}"
            for update in self.updates
        ]

    def users_from_updates(self):
        return {update["user"] for update in self.updates}


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
    except HTTPError:
        raise NotificationError("Error creating GitHub issue")


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
    except HTTPError:
        raise NotificationError("Error closing GitHub issue")


def update_issue(airlock_event: AirlockEvent, github_api=None):
    github_api = github_api or _get_github_api()
    updates = airlock_event.describe_updates()
    try:
        update_output_checking_issue(
            airlock_event.release_request_id,
            updates,
            airlock_event.org,
            airlock_event.repo,
            github_api,
        )
    except HTTPError:
        raise NotificationError("Error creating GitHub issue comment")


def email_author(airlock_event: AirlockEvent):
    match airlock_event.event_type:
        case EventType.REQUEST_RELEASED:
            send_request_released_email(airlock_event)
        case EventType.REQUEST_REJECTED:
            send_request_rejected_email(airlock_event)
        case EventType.REQUEST_RETURNED:
            send_request_returned_email(airlock_event)
        case _:
            assert airlock_event.event_type == EventType.REQUEST_UPDATED
            # Skip email if ALL updates were made by the request author
            if airlock_event.users_from_updates() == {
                airlock_event.request_author.username
            }:
                return
            send_request_updated_email(airlock_event)


EVENT_NOTIFICATIONS = {
    EventType.REQUEST_SUBMITTED: [create_issue],
    EventType.REQUEST_WITHDRAWN: [close_issue],
    EventType.REQUEST_APPROVED: [],
    EventType.REQUEST_RELEASED: [email_author, close_issue],
    EventType.REQUEST_REJECTED: [email_author, close_issue],
    EventType.REQUEST_RETURNED: [email_author, update_issue],
    EventType.REQUEST_RESUBMITTED: [update_issue],
    EventType.REQUEST_UPDATED: [email_author, update_issue],
    EventType.REQUEST_PARTIALLY_REVIEWED: [update_issue],
    EventType.REQUEST_REVIEWED: [update_issue],
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
