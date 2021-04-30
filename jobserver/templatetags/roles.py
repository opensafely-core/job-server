from django import template

from jobserver.authorization.parsing import parse_roles


register = template.Library()


@register.filter
def role_description(role_path):
    role = parse_roles([role_path])[0]

    return role.description.strip()
