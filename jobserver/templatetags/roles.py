from django import template

from jobserver.authorization.parsing import parse_role


register = template.Library()


@register.filter
def role_description(role_path):
    role = parse_role(role_path)

    return role.description.strip()
