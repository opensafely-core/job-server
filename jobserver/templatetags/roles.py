from django import template
from first import first

from jobserver.authorization.parsing import parse_roles


register = template.Library()


@register.filter
def role_description(role_path):
    try:
        role = first(parse_roles([role_path]))
    except (ImportError, ValueError):  # unknown Role
        return ""

    return role.description.strip()
