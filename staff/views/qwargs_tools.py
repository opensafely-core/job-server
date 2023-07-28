import functools

from django.db.models import Q


def qwargs(fields, query, expression="icontains", operator=Q.__or__):
    """
    Build a Q object across the given fields with the given query

    By default this ORs together a group of __icontains conditions.
    """
    return functools.reduce(
        operator, (Q(**{f"{field}__{expression}": query}) for field in fields)
    )
