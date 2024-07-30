## -*- coding: utf-8 -*-

# Code below taken from
# https://github.com/hynek/first/blob/b95e3ee504d4fcd735b056c472d35148e341a80a/first.py
# included under the MIT license as detailed below.

# Copyright (c) 2012 Hynek Schlawack
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
first
=====

first is the function you always missed in Python.

In the simplest case, it returns the first true element from an iterable:

>>> from first import first
>>> first([0, False, None, [], (), 42])
42

Or None if there is none:

>>> from first import first
>>> first([]) is None
True
>>> first([0, False, None, [], ()]) is None
True

It also supports the passing of a key argument to help selecting the first
match in a more advanced way.

>>> from first import first
>>> first([1, 1, 3, 4, 5], key=lambda x: x % 2 == 0)
4

:copyright: (c) 2012 by Hynek Schlawack.
:license: MIT, see LICENSE for more details.

"""

__title__ = 'first'
__version__ = '2.0.2'
__author__ = 'Hynek Schlawack'
__license__ = 'MIT'
__copyright__ = 'Copyright 2012 Hynek Schlawack'


def first(iterable, default=None, key=None):
    """
    Return first element of `iterable` that evaluates true, else return None
    (or an optional default value).

    >>> first([0, False, None, [], (), 42])
    42

    >>> first([0, False, None, [], ()]) is None
    True

    >>> first([0, False, None, [], ()], default='ohai')
    'ohai'

    >>> import re
    >>> m = first(re.match(regex, 'abc') for regex in ['b.*', 'a(.*)'])
    >>> m.group(1)
    'bc'

    The optional `key` argument specifies a one-argument predicate function
    like that used for `filter()`.  The `key` argument, if supplied, must be
    in keyword form.  For example:

    >>> first([1, 1, 3, 4, 5], key=lambda x: x % 2 == 0)
    4

    """
    if key is None:
        for el in iterable:
            if el:
                return el
    else:
        for el in iterable:
            if key(el):
                return el

    return default
