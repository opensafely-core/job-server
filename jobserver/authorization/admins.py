from environs import Env

from ..models import User
from .roles import SuperUser


env = Env()


def get_admins():
    """
    Get a list of Admin usernames from the env

    Auth is handled via GitHub OAuth so these are GitHub usernames.
    """
    admin_users = env.list("ADMIN_USERS")

    # remove whitespace and only return non-empty strings
    return [u.strip() for u in admin_users if u]


def ensure_admins(usernames):
    """
    Given an iterable of username strings, ensure they have the SuperUser role
    """
    if not usernames:
        raise Exception("No admin users configured, aborting")

    admins = User.objects.filter(username__in=usernames)

    missing = set(usernames) - {u.username for u in admins}
    if missing:
        sorted_missing = sorted(missing)
        raise Exception(f"Unknown users: {', '.join(sorted_missing)}")

    for admin in admins:
        admin.roles.append(SuperUser)
        admin.save()
