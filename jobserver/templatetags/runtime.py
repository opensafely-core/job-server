from django import template

from ..runtime import Runtime


register = template.Library()


@register.simple_tag
def runtime(r: Runtime):
    if not r:
        return "-"

    return f"{r.hours:02d}:{r.minutes:02d}:{r.seconds:02d}"
