from django import template
from furl import furl


register = template.Library()


@register.simple_tag(takes_context=True)
def url_with_querystring(context, **kwargs):
    """
    Build a new url with updated query parameters.

    Takes context so we can get the request to get the current URL with its
    existing query params.  Then we update those with any kwargs passed in.

    We need to handle pagination as a bit of an edge case.  We don't want to
    blindly apply filters since a user could easily get no results due to
    pagination.  Instead we remove the page arg only when a new filter is added
    to the URL.
    """
    request = context["request"]
    f = furl(request.get_full_path())

    for k, v in kwargs.items():
        f.args[k] = v

    # avoid deleting page when it's explicitly in kwargs
    if "page" not in kwargs and "page" in f.args:
        del f.args["page"]

    return f.url


@register.simple_tag(takes_context=True)
def url_without_querystring(context, **kwargs):
    """
    Build a new url with the given query parameters removed.

    Takes context so we can get the request to get the current URL with its
    existing query params.  Then we update those with any kwargs passed in.

    We also blindly remove the page argument since we want to wipe the current
    page whenever removing a filter.
    """
    request = context["request"]
    f = furl(request.get_full_path())

    for k in kwargs.keys():
        del f.args[k]

    if "page" in f.args:
        del f.args["page"]

    return f.url
