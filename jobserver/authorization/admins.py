from django.db import transaction
from environs import Env

from ..models import User
from .roles import CoreDeveloper


env = Env()


def get_admins():
    """
    Get a list of Admin usernames from the env

    Auth is handled via GitHub OAuth so these are GitHub usernames.
    """
    admin_users = env.list("ADMIN_USERS", default=[])

    # remove whitespace and only return non-empty strings
    return [u.strip() for u in admin_users if u]


@transaction.atomic()
def ensure_admins(usernames):
    """
    Given an iterable of username strings, ensure they have the CoreDeveloper
    role which we to denote administrators.
    """
    for user in User.objects.all():
        try:
            user.roles.remove(CoreDeveloper)
        except ValueError:
            pass
        user.save()

    admins_to_be = User.objects.filter(username__in=usernames)

    missing = set(usernames) - {u.username for u in admins_to_be}
    if missing:
        sorted_missing = sorted(missing)
        raise Exception(f"Unknown admin usernames: {', '.join(sorted_missing)}")

    for admin in admins_to_be:
        admin.roles.append(CoreDeveloper)
        admin.save()
