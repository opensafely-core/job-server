from dataclasses import dataclass
from enum import Enum

from requests.exceptions import HTTPError
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response

from jobserver.api.authentication import get_backend_from_token
from jobserver.github import _get_github_api
from jobserver.models import User, Workspace

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
    REQUEST_UPDATED = "request updated"


class UpdateType(Enum):
    FILE_ADDED = "file added"
    FILE_WITHDRAWN = "file withdrawn"
    CONTEXT_EDITED = "context edited"
    CONTROLS_EDITED = "controls edited"
    COMMENT_ADDED = "comment added"


@dataclass(frozen=True)
class AirlockEvent:
    event_type: EventType
    update_type: UpdateType | None
    workspace: Workspace
    release_request_id: str
    group: str | None
    request_author: User
    user: User

    @classmethod
    def from_payload(cls, data):
        event_type = EventType[data.get("event_type").upper()]
        update_type = data.get("update_type")

        request_author = User.objects.get(username=data.get("request_author"))
        username = data.get("user")
        if username == request_author.username:
            user = request_author
        else:
            user = User.objects.get(username=username)

        if update_type:
            update_type = UpdateType[update_type.upper()]

        workspace = Workspace.objects.get(name=data.get("workspace"))

        return cls(
            event_type=event_type,
            update_type=update_type,
            workspace=workspace,
            release_request_id=data.get("request"),
            group=data.get("group"),
            request_author=request_author,
            user=user,
        )

    def describe_event(self):
        return self.event_type.value

    def describe_update(self):
        return f"{self.update_type.value} (filegroup {self.group})"


def create_issue(airlock_event: AirlockEvent, github_api=None):
    github_api = github_api or _get_github_api()
    try:
        create_output_checking_issue(
            airlock_event.workspace,
            airlock_event.release_request_id,
            airlock_event.request_author,
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
            github_api,
        )
    except HTTPError:
        raise NotificationError("Error closing GitHub issue")


def update_issue(airlock_event: AirlockEvent, github_api=None):
    github_api = github_api or _get_github_api()
    update = airlock_event.describe_update()
    try:
        update_output_checking_issue(
            airlock_event.release_request_id,
            airlock_event.user,
            update,
            github_api,
        )
    except HTTPError:
        raise NotificationError("Error creating GitHub issue comment")


def email_author(airlock_event: AirlockEvent): ...


EVENT_NOTIFICATIONS = {
    EventType.REQUEST_SUBMITTED: [create_issue],
    EventType.REQUEST_WITHDRAWN: [close_issue],
    EventType.REQUEST_RELEASED: [email_author, close_issue],
    EventType.REQUEST_REJECTED: [email_author, close_issue],
    EventType.REQUEST_UPDATED: [email_author, update_issue],
}


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
def airlock_event_view(request):
    token = request.headers.get("Authorization")
    # do token authentication
    get_backend_from_token(token)

    airlock_event = AirlockEvent.from_payload(request.data)

    try:
        handle_notifications(airlock_event)
    except NotificationError as e:
        return Response({"status": "error", "message": str(e)}, status=201)
    return Response({"status": "ok"}, status=201)


def handle_notifications(airlock_event: AirlockEvent):
    for notify_fn in EVENT_NOTIFICATIONS[airlock_event.event_type]:
        notify_fn(airlock_event)
