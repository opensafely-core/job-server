import textwrap
from urllib.parse import urlparse

from django.core.exceptions import BadRequest


def build_spa_base_url(full_path, file_path):
    """
    Break the full path of a page down into the URL path without any file path

    Given a URL such as

        /org/project/workspace/releases/string/path/to/file.csv

    we want to tell the SPA about the page path

        /org/project/workspace/releases/string/

    """
    return full_path.removesuffix(file_path)


def dotted_path(cls):
    """Get the dotted path for a given class"""
    return f"{cls.__module__}.{cls.__qualname__}"


def is_safe_path(path):
    """If `path` is safe, then returns `True`. Otherwise returns `False`.

    A safe path has neither a scheme (e.g. "https") nor a location (e.g.
    "www.opensafely.org").
    """
    parse_result = urlparse(path)
    return not (parse_result.scheme or parse_result.netloc)


def raise_if_not_int(value):
    try:
        int(value)
    except ValueError:
        raise BadRequest


def strip_whitespace(text):
    """
    Strip various whitespace from text

    When we create messages, for example for GitHub Issues or Slack, we use
    triple quoted strings so we have a template like structure.  Because of the
    way triple-quoted strings work we end up with a leading newline, and `\n
    ` at the end of the string.  This function strips all of that away while
    allowing us to have readable body templates.
    """
    text = text.strip("\n")

    text = textwrap.dedent(text)

    return text.strip("\n")


def set_from_qs(qs, field="pk"):
    return set(qs.values_list(field, flat=True))
