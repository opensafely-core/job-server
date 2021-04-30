from django import template
from first import first

from jobserver.authorization.parsing import parse_roles


register = template.Library()


@register.filter
def role_description(role_path):
    role = first(parse_roles([role_path]))

    return role.description.strip()
