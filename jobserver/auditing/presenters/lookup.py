from jobserver.models import AuditableEvent

from . import project_members
from .exceptions import UnknownPresenter


def get_presenter(event):
    """
    Look up a presenter from the given AuditableEvent

    We need to map AuditableEvent instances to their presenter using their type
    field.  AuditableEvents have a .presenter property as a convenience wrapper
    for this function.

    The lookup dict in this function is expected to grow to handle every type
    of event because we can't shoe horn it into the Type enumeration on
    AuditableEvent, and arguably shouldn't.
    """
    func_lut = {
        AuditableEvent.Type.PROJECT_MEMBER_ADDED: project_members.added,
        AuditableEvent.Type.PROJECT_MEMBER_REMOVED: project_members.removed,
        AuditableEvent.Type.PROJECT_MEMBER_UPDATED_ROLES: project_members.updated_roles,
    }

    try:
        return func_lut[event.type]
    except KeyError as e:
        raise UnknownPresenter from e
