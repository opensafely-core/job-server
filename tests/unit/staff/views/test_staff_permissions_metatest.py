from collections.abc import Iterable, Iterator

import pytest
from django.http import HttpRequest
from django.test import RequestFactory
from django.urls.resolvers import URLPattern, URLResolver

from staff import urls as staff_urls

from ....factories import UserFactory


def iter_urlpatterns(
    patterns: Iterable[URLPattern | URLResolver],
) -> Iterator[URLPattern]:  # pragma: no cover
    """
    Walk through nested include() URL groups and return only the
    actual routes.
    """

    for pattern in patterns:
        if isinstance(pattern, URLPattern):
            yield pattern
        elif isinstance(pattern, URLResolver):
            # Include nested patterns from include() calls.
            yield from iter_urlpatterns(pattern.url_patterns)


def test_staff_urls_require_permission(rf: RequestFactory) -> None:  # pragma: no cover
    """
    This test does a broad sweep over the Staff Area URLs to make sure we are
    not missing basic unauthorized permission checks.

    In simple terms it:
    - looks at every staff URL (including ones inside `include()` blocks)
    - keeps only the ones that point at `staff.views.*`
    - calls each view with a simple `GET` request and placeholder URL arguments
    - expects the view to raise some kind of error (usually a permission error)
    - fails the test only if the view returns normally

    The view could fail for other reasons, but this test is a backstop for any
    potential missing permission check tests.
    """

    for pattern in iter_urlpatterns(staff_urls.urlpatterns):
        if not pattern.callback.__module__.startswith("staff.views."):
            continue

        kwargs: dict[str, str] = {name: "test" for name in pattern.pattern.converters}
        request: HttpRequest = rf.get("/")
        request.user = UserFactory()

        try:
            pattern.callback(request, **kwargs)
        except Exception:
            # Any exception is fine here; permission checks typically raise.
            continue
        else:
            # A normal return suggests the view skipped access checks.
            pytest.fail(f"Expected an exception for staff URL '{pattern.pattern}'")
