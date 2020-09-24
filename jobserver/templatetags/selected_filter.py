from django import template


register = template.Library()


@register.simple_tag(takes_context=True)
def is_filter_selected(context, *, key, value, **kwargs):
    """
    Check if the given filter [key] is currently active

    We serialise selected filters to query args.  The given `key` is used to
    look up the value associated with that key in the request's query args.
    This is then compared to the given value to see if the element this was
    used with is considered active.

    It is expected that this template tag will be used to mark filters on list
    pages as active/inactive.
    """
    request = context["request"]

    #  query args are always strings so ensure the value we compare a potential
    # arg to is also a string
    value = str(value)

    arg = request.GET.get(key)

    if arg is None:
        return False

    if arg != value:
        return False

    return True
