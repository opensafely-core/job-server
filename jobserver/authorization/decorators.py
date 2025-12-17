from functools import wraps

from django.core.exceptions import PermissionDenied

from .permissions import backend_manage
from .utils import has_permission


def require_permission(permission):
    """
    Decorator for views which require a given Permission

    This doesn't accept any context currently.
    """

    def decorator_require_permission(f):
        @wraps(f)
        def wrapper_require_role(request, *args, **kwargs):
            if not has_permission(request.user, permission):
                raise PermissionDenied

            return f(request, *args, **kwargs)

        return wrapper_require_role

    return decorator_require_permission


require_manage_backends = require_permission(backend_manage)
