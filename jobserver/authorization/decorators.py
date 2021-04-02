from functools import wraps

from django.http import HttpResponseForbidden

from .roles import SuperUser
from .utils import has_role


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


require_superuser = require_role(SuperUser)
