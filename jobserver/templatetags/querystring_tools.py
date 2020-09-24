from django import template
from furl import furl


register = template.Library()


@register.simple_tag(takes_context=True)
def url_with_querystring(context, **kwargs):
    """
    Build a new url with updated query parameters.

    Takes context so we can get the request to get the current URL with its
    existing query params.  Then we update those with any kwargs passed in.
    """
    request = context["request"]
    f = furl(request.get_full_path())

    for k, v in kwargs.items():
        f.args[k] = v

    return f.url


@register.simple_tag(takes_context=True)
def url_without_querystring(context, **kwargs):
    """
    Build a new url with the given query parameters removed.

    Takes context so we can get the request to get the current URL with its
    existing query params.  Then we update those with any kwargs passed in.
    """
    request = context["request"]
    f = furl(request.get_full_path())

    for k in kwargs.keys():
        del f.args[k]

    return f.url
