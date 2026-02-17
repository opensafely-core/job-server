from jobserver.models import Project, User


def lookup_project(*, pk: str, default: str = "a Project") -> Project | str:
    """Resolve a project by pk, falling back to a display string if it's missing."""

    try:
        return Project.objects.get(pk=pk)
    except (Project.DoesNotExist, ValueError):
        # Handle a ValueError here because Django will (helpfully!) try to cast
        # the given pk to an int for BigAutoFields. However AuditableEvent's
        # target_id and parent_id are TextFields which default to an empty
        # string, we can't guarantee that's been populated, and int("") raises
        # a ValueError.
        return default


def lookup_user(username: str) -> User | str:
    """Resolve a user by username, falling back to a display string if unknown."""

    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        return username if username else "Unknown User"


def roles_str_to_class_name_str(roles_string: str) -> str:
    """
    Turn saved roles into display names

    We store roles as the repr's of their values, eg

        <class 'jobserver.authorization.roles.ProjectDeveloper'>

    This allows us to keep the creation of field changes generic.  However
    we need to turn these into something meaningful for display.
    """
    roles = roles_string.split(",")
    names = [r.rsplit(".")[-1] for r in roles]
    return ", ".join(names)
