from ..models import User
from .utils import roles_for


# A global role can be assigned to a User independently of ProjectMembership.
# It either does not relate to Projects or grants permissions across ALL projects.

GLOBAL_ROLES = roles_for(User)

GLOBAL_ROLE_NAMES = [role.__name__ for role in GLOBAL_ROLES]
