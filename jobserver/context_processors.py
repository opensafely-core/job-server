import functools

from django.urls import reverse


def _is_active(request, prefix):
    return request.path.startswith(prefix)


def nav(request):
    _active = functools.partial(_is_active, request)

    options = [
        {
            "name": "Jobs",
            "is_active": _active(reverse("job-list")),
            "url": reverse("job-list"),
        },
        {
            "name": "Status",
            "is_active": _active(reverse("status")),
            "url": reverse("status"),
        },
    ]

    return {"nav": options}
