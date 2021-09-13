import os

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from markdown import markdown


register = template.Library()


@register.simple_tag
def snippet(path):
    full_path = os.path.join(settings.BASE_DIR, "snippets", (path + ".md"))
    with open(full_path) as f:
        text = f.read()
    content = markdown(text)
    return mark_safe(content)
