from enum import StrEnum, auto


# Using auto() with StrEnum results in the lower-cased member name as the
# value (https://docs.python.org/3/library/enum.html#enum.StrEnum)
class Permission(StrEnum):
    """Represents the set of permissions available within jobserver.

    StrEnum Members:
        Permission values are lower-cased strings derived from the
        member names via `auto()`.
    """

    APPLICATION_MANAGE = auto()

    BACKEND_MANAGE = auto()

    JOB_CANCEL = auto()
    JOB_RUN = auto()

    ORG_CREATE = auto()

    PROJECT_MANAGE = auto()

    RELEASE_FILE_DELETE = auto()
    RELEASE_FILE_UPLOAD = auto()
    RELEASE_FILE_VIEW = auto()

    REPO_SIGN_OFF_WITH_OUTPUTS = auto()

    SNAPSHOT_CREATE = auto()
    SNAPSHOT_PUBLISH = auto()

    STAFF_AREA_ACCESS = auto()

    UNRELEASED_OUTPUTS_VIEW = auto()

    USER_MANAGE = auto()

    WORKSPACE_ARCHIVE = auto()
    WORKSPACE_CREATE = auto()
    WORKSPACE_TOGGLE_NOTIFICATIONS = auto()
