def dotted_path(cls):
    """Get the dotted path for a given class"""
    return f"{cls.__module__}.{cls.__qualname__}"
