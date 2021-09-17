from django import template

from ..snippets import build_path, render_snippet


register = template.Library()


@register.simple_tag
def snippet(name):
    path = build_path(name)
    return render_snippet(path)
