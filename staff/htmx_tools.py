import copy

from first import first

from .querystring_tools import merge_query_args


def get_next_url(query_args, default=""):
    try:
        next_url = query_args.pop("next")
    except KeyError:
        # QueryDict.pop() raises a KeyError if the key doesn't exist and we
        # can't pass a default value.  So normal to None which lets us decide
        # what we want to do with it below.
        next_url = None

    # Django's QueryDict returns items as lists (which is correct for query
    # args), but we only want the first one.  QueryDict would handle this
    # for us but we've .pop()'d the value which gives us the list repr.
    if next_url is not None:
        next_url = first(next_url)

    if next_url:
        return next_url

    return default


def get_redirect_url(query_dict, default_url, extra_args):
    # HTMX clients should pass their current path, and any query args,
    # in the template.  We use those to know where to redirect back to,
    # and want to preserve any remaining query args.

    # copy the QueryDict so we can mutate to pop the "next" item.
    query_args = copy.deepcopy(query_dict)

    # get the value of next to redirect to but fall back to a sensible
    # location if there's no valid next param
    next_url = get_next_url(query_args, default=default_url)

    # add the org slug so consumers get the result of the input
    f = merge_query_args(query_args, extra_args)

    # set the passed next_url as our path now
    f.path = next_url

    return f.url
