def compare(fake, real):
    """
    Compare outputs of Fake* instances to those from API instances

    Fake API instances return partial, non-real data from the methods they
    implement.  For tests we haven't found the need to have those responses be
    real data, but we still what their shape and values to be correct in terms
    of the API response schemas.  This function checks the correctness of those
    values.
    """

    assert type(fake) == type(real)

    if isinstance(fake, list):
        for x, y in zip(fake, real):
            compare(x, y)
        return

    if isinstance(fake, str | int):
        return

    for key, value in fake.items():
        assert key in real
        assert isinstance(value, type(real[key]))

        if isinstance(value, dict):
            compare(fake[key], real[key])
