from collections.abc import Callable
from dataclasses import dataclass

from django.http import HttpRequest
from django.urls import reverse


@dataclass
class NavItem:
    name: str
    url_name: str
    predicate: Callable[[HttpRequest], bool] = lambda request: True


def iter_nav(items, request, is_active):
    for item in items:
        if not item.predicate(request):
            continue

        url = reverse(item.url_name)
        yield {
            "name": item.name,
            "is_active": is_active(url),
            "url": url,
        }
