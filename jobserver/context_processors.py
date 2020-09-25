import functools

from django.urls import reverse


def _is_active(request, prefix):
    return request.path.startswith(prefix)


def nav(request):
    _active = functools.partial(_is_active, request)

    options = [
        {
            "name": "Workspaces",
            "is_active": _active(reverse("workspace-list")),
            "url": reverse("workspace-list"),
        },
        {
            "name": "Jobs",
            "is_active": _active(reverse("job-list")),
            "url": reverse("job-list"),
        },
    ]

    return {"nav": options}
