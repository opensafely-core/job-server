from django import template

from ..snippets import render_snippet


register = template.Library()


@register.simple_tag
def snippet(key):
    return render_snippet(key)
