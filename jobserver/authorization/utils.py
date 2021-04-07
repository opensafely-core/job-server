import itertools


def has_permission(user, permission):
    if not user.is_authenticated:
        return False

    roles = user.roles

    # Flatten each Roles permissions list into a single iterable
    permissions = itertools.chain.from_iterable(r.permissions for r in roles)

    # convert the itertools.chain generator into a set so we can check membership
    permissions = set(permissions)

    # return a boolean for whether the requested permission is in that set
    return permission in permissions


def has_role(user, role):
    if not user.is_authenticated:
        return False

    return role in user.roles
