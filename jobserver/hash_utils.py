"""Provides a pair of methods for converting between sequential IDs and random-looking
hex strings.

>>> for m in range(5):
...   print(hash(m))
...
0000
1edd
3dba
5c97
7b74
>>> for m in range(16 ** 4):
...   assert unhash(hash(m)) == m
...
>>>

Implementation is based on modular multiplicative inverses, as described in
https://stackoverflow.com/a/38240325.

To produce a string of length l, we find N = 16 ** l.

Then, for odd k, for every m between 0 and N - 1, we can map m to m_hash:

    m_hash = (m * k) % N.

Each m maps to a different m_hash, and so we can unambigously map from m_hash to m:

    m = (m_hash * inv_k) % N

where inv_k is the multiplicative inverse of k modulo N:

    inv_k = pow(k, -1, N)

To convert m_hash to a string of length l, we convert it to a hex value and then right
pad it with zeros.

The following output should demonstrate how this works in practice:

>>> l = 4
>>> N = 16 ** l
>>> N
65536
>>> k = 999
>>> inv_k = pow(k, -1, N)
>>> inv_k
24535
>>>
>>> m = 1181
>>> m_hash = (m * k) % N
>>> m_hash
171
>>> (m_hash * inv_k) % N
1181
>>> (m_hash * inv_k) % N == m
True
>>>
>>> hex(m_hash)
'0xab'
>>> h = hex(m_hash)[2:].rjust(l, "0")
>>> h
'00ab'
>>> int(h, 16)
171
>>> int(h, 16) == m_hash
True
"""

from django.contrib.auth.hashers import make_password
from django.http import Http404


# Sensible defaults.  There are 2 ** 16 unique hex strings of length 4.  This is
# probably enough for things like project applications.  (Using up 1 string per day will
# last ~180 years.)
DEFAULT_LENGTH = 4
DEFAULT_KEY = 7901


def hash(m, length=DEFAULT_LENGTH, key=DEFAULT_KEY):  # noqa: A001
    """Hash integer m to give a string."""

    N = 16**length
    assert key % 2 == 1

    if not 0 <= m < N:
        raise ValueError(f"Input m ({m}) must satisfy 0 <= m < {N}")

    m_hash = (m * key) % N
    assert 0 <= m_hash < N

    return hex(m_hash)[2:].rjust(length, "0")


def hash_user_pat(token):
    """
    Utility function to hash a token for User PATs

    The hashingn algorithm for this is controlled by the PASSWORD_HASHERS
    setting.
    """
    return make_password(token, salt="user_pat")


def unhash(h, length=DEFAULT_LENGTH, key=DEFAULT_KEY):
    """Unhash string h to give an integer."""

    N = 16**length
    assert key % 2 == 1

    if len(h) != length:
        raise ValueError(f"Input h ({h}) must be {length} characters long")

    inv_key = pow(key, -1, N)

    m_hash = int(h, 16)
    assert 0 <= m_hash < N

    return (m_hash * inv_key) % N


def unhash_or_404(h, length=DEFAULT_LENGTH, key=DEFAULT_KEY):
    """Unhash string h, raising 404 if h is invalid."""

    try:
        return unhash(h, length, key)
    except ValueError:
        raise Http404
