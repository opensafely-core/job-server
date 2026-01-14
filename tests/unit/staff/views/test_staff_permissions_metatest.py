from collections.abc import Iterable, Iterator

import pytest
from django.core.exceptions import PermissionDenied
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


def describe_staff_view(pattern: URLPattern) -> str:  # pragma: no cover
    callback = pattern.callback
    view_class = getattr(callback, "view_class", None)
    if view_class is not None:
        view_name = f"{view_class.__module__}.{view_class.__qualname__}"
    else:
        callback_name = getattr(callback, "__qualname__", callback.__name__)
        view_name = f"{callback.__module__}.{callback_name}"

    return f"{view_name}"


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_staff_urls_require_permission(
    rf: RequestFactory, method: str
) -> None:  # pragma: no cover
    """
    This test does a broad sweep over the Staff Area URLs to make sure we are
    not missing basic unauthorized permission checks.

    In simple terms it:
    - looks at every staff URL (including ones inside `include()` blocks)
    - keeps only the ones that point at `staff.views.*`
    - calls each view with a request for a user without Staff Area permissions
    - expects the view to raise `PermissionDenied`
    """

    failures: list[str] = []

    for pattern in iter_urlpatterns(staff_urls.urlpatterns):
        if not pattern.callback.__module__.startswith("staff.views."):
            continue
        view_description = describe_staff_view(pattern)

        kwargs: dict[str, str] = {name: "test" for name in pattern.pattern.converters}
        if method == "GET":
            request: HttpRequest = rf.get("/")
        else:
            request: HttpRequest = rf.post("/", data={"placeholder": "value"})
        request.user = UserFactory()

        try:
            pattern.callback(request, **kwargs)
        # good case, where we get PermissionDenied
        except PermissionDenied:
            pass
        # failing case, where the exception isn't PermissionDenied
        except Exception as exc:
            failures.append(
                "Expected PermissionDenied from "
                f"{view_description} for {method}, got "
                f"{exc.__class__.__name__}: {exc}"
            )
        # failing case, where no exception is raised at all
        else:
            failures.append(
                "Expected PermissionDenied from "
                f"{view_description} for {method}, found no exception"
            )

    if failures:
        pytest.fail("\n".join(failures))
