# Hotfix for HTML escaping issue in `slippers` library
import slippers.templatetags.slippers
from django.utils.html import format_html


def safe_attr_string(key, value):
    key = key.replace("_", "-")

    if isinstance(value, bool):
        return key if value else ""

    return format_html('{}="{}"', key, value)


def apply_patch():
    slippers.templatetags.slippers.attr_string = safe_attr_string
