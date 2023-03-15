from furl import furl


def merge_query_args(existing, updates):
    f = furl()
    f.args.update(existing)
    f.args.update(updates)

    # return a furl instance so we can use to pull the URL from it, or combine
    # it with more data
    return f
