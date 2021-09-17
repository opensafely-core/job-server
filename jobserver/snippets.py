import os

from django.conf import settings
from django.utils.safestring import mark_safe
from markdown import markdown


def build_path(name):
    name = f"{name}.md"
    return os.path.join(settings.BASE_DIR, "snippets", name)


def expand_snippets(spec):
    """
    Expand spec values using snippets if necessary

    We allow any field in a spec to have a snippet associated with it using the
    <snippet> string.  When this value is encountered we convert it into a path
    using the context of that value, like so:

        <spec key>-[fieldsetN-][fieldN-]<key>

    """
    key = str(spec["key"])

    # top level keys
    for k, value in spec.items():
        name = f"{key}-{k}"
        spec[k] = replace_value_with_snippet(name, value)

    # fieldsets
    for i, fieldset in enumerate(spec["fieldsets"]):
        for k, value in fieldset.items():
            name = f"{key}-fieldset{i}-{k}"
            spec["fieldsets"][i][k] = replace_value_with_snippet(name, value)

        # fields
        for j, field in enumerate(fieldset["fields"]):
            for k, value in field.items():
                name = f"{key}-fieldset{i}-field{j}-{k}"
                spec["fieldsets"][i]["fields"][j][k] = replace_value_with_snippet(
                    name, value
                )

    return spec


def render_snippet(path):
    with open(path) as f:
        text = f.read()

    content = markdown(text)

    return mark_safe(content)


def replace_value_with_snippet(name, value):
    if value != "<snippet>":
        return value

    path = build_path(name)
    return render_snippet(path)
