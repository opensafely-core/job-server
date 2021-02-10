from environs import Env

from jobserver.models import User


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
    Given an iterable of username strings, set the is_superuser bit
    """
    if not usernames:
        raise Exception("No admin users configured, aborting")

    admins = User.objects.filter(username__in=usernames)

    missing = set(usernames) - set(u.username for u in admins)
    if missing:
        sorted_missing = sorted(missing)
        raise Exception(f"Unknown users: {', '.join(sorted_missing)}")

    # reset all users permissions first
    User.objects.update(is_staff=False, is_superuser=False)

    # update configured users to be admins
    admins.update(is_staff=True, is_superuser=True)
