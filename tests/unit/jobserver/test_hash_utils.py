import pytest
from django.http import Http404

from jobserver import hash_utils


def test_roundtrip_1():
    # Verify that for every integer between 0 and 65535, hashing the integer and
    # unhashing the result returns the same integer.
    for m in range(2**16):
        assert hash_utils.unhash(hash_utils.hash(m)) == m


def test_roundtrip_2():
    # Verify that for every hash string between "0000" and "ffff", unhashing the has and
    # hashing the result returns the same string.
    for m_hash in range(2**16):
        # Construct a hash from an integer.  For the meaning of m_hash and h, see module
        # docstring in hash_utils.py.
        h = hex(m_hash)[2:].rjust(4, "0")
        assert hash_utils.hash(hash_utils.unhash(h)) == h


def test_invalid_hash_input():
    with pytest.raises(ValueError):
        hash_utils.hash(-1)

    with pytest.raises(ValueError):
        hash_utils.hash(2**16 + 1)


def test_invalid_unhash_input():
    with pytest.raises(ValueError):
        hash_utils.unhash("123")

    with pytest.raises(ValueError):
        hash_utils.unhash("12345")

    with pytest.raises(ValueError):
        hash_utils.unhash("WXYZ")


def test_unhash_or_404():
    assert hash_utils.unhash_or_404("0000") == 0

    with pytest.raises(Http404):
        hash_utils.unhash_or_404("WXYZ")
