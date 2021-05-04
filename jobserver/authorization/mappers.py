"""
Functions to get Roles from  Model <-> User relationships

Local Roles are tied to a particular Model.  These mapper functions take the
object you are likely to have as a context (eg a Project), the User you are
querying the Roles or Permissions of, and return an iterable of Roles for that
optional relationship.

Each function is expected to handle the lookup of Roles in a given relationship.
"""


def get_org_roles_for_user(org, user):
    try:
        return org.members.get(user=user).roles
    except org.members.model.DoesNotExist:
        return []


def get_project_roles_for_user(project, user):
    try:
        return project.members.get(user=user).roles
    except project.members.model.DoesNotExist:
        return []
