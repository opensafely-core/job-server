from functools import wraps

from django.http import HttpResponseForbidden

from .permissions import manage_backends
from .utils import has_permission, has_role


def require_permission(permission):
    """
    Decorator for views which require a given Permission

    This doesn't accept any context currently.
    """

    def decorator_require_permission(f):
        @wraps(f)
        def wrapper_require_role(request, *args, **kwargs):
            if not has_permission(request.user, permission):
                return HttpResponseForbidden()

            return f(request, *args, **kwargs)

        return wrapper_require_role

    return decorator_require_permission


def require_role(role):
    """Decorator for views which require a given Role"""

    def decorator_require_role(f):  # sigh
        @wraps(f)
        def wrapper_require_role(request, *args, **kwargs):
            if not has_role(request.user, role):
                return HttpResponseForbidden()

            return f(request, *args, **kwargs)

        return wrapper_require_role

    return decorator_require_role


require_manage_backends = require_permission(manage_backends)
