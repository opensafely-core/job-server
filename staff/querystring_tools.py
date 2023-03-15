from furl import furl


def get_next_url(query_dict, default=""):
    f = furl()
    f.args.update(query_dict)

    return f.args.get("next", default)
