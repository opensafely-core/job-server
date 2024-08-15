def first(iterable, default=None, key=None):
    if key is None:
        return next((i for i in iterable if i), default)
    else:
        return next((i for i in iterable if key(i)), default)
