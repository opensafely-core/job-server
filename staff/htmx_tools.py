from furl import furl


def get_redirect_url(query_dict, default_url, extra_args):
    # HTMX clients should pass their current path, and any query args,
    # in the template.  We use those to know where to redirect back to,
    # and want to preserve any remaining query args.
    f = furl()
    f.args.update(query_dict)

    # get the value of next to redirect to but fall back to a sensible
    # location if there's no valid next param
    f.path = f.args.pop("next", default_url)

    # add the org slug so consumers get the result of the input
    # add any other args to the object
    f.args.update(extra_args)

    return f.url
