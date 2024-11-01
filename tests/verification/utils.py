import inspect


def assert_deep_type_equality(fake, real):
    """
    Do two objects have the same types, compared deeply?

    Fake API instances return dummy data from the methods they implement.  We
    want to be able to validate that at least the returned types are the same.

    For example, if `fake` is a list, is `real` a list, and do the
    corresponding elements of those lists also have the same types?

    Works for str, int, list, dict, recursively. These are currently the types
    we expect the relevant API endpoints to return.
    """

    assert type(fake) is type(real)

    if isinstance(fake, list):
        for x, y in zip(fake, real):
            assert_deep_type_equality(x, y)
        return

    if isinstance(fake, str | int):
        return

    for key, value in fake.items():
        assert key in real and isinstance(value, type(real[key]))

        if isinstance(value, dict):
            assert_deep_type_equality(fake[key], real[key])


def _get_public_method_signatures(cls, ignored_methods):
    return {
        name: inspect.signature(method)
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction)
        if not name.startswith("_") and name not in ignored_methods
    }


def assert_public_method_signature_equality(first, second, ignored_methods=None):
    """Do two objects have the same public methods and signatures?"""
    if not ignored_methods:
        ignored_methods = []
    first_methods = _get_public_method_signatures(first, ignored_methods)
    second_methods = _get_public_method_signatures(second, ignored_methods)

    assert set(first_methods) == set(second_methods), "methods mismatch"

    # Check if every public method of the first class is in the second class
    # with the same signature.
    for name, sig in first_methods.items():
        assert second_methods[name] == sig, "signature mismatch"
