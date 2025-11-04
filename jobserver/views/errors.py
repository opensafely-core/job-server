from django.core.exceptions import TooManyFieldsSent
from django.template.response import TemplateResponse


def bad_request(request, exception=None):
    if isinstance(exception, TooManyFieldsSent):
        return TemplateResponse(
            request,
            "error.html",
            status=413,
            context={
                "error_code": "413",
                "error_name": "Too many fields submitted",
                "error_message": "Your submission contained too many fields. Please reduce the number of selected items and try again.",
            },
        )

    return TemplateResponse(
        request,
        "error.html",
        status=400,
        context={
            "error_code": "400",
            "error_name": "Bad request",
            "error_message": "An error has occurred displaying this page.",
        },
    )


def csrf_failure(request, reason=""):
    return TemplateResponse(
        request,
        "error.html",
        status=400,
        context={
            "error_code": "CSRF",
            "error_name": "CSRF Failed",
            "error_message": "The form was not able to submit.",
        },
    )


def page_not_found(request, exception=None):
    return TemplateResponse(
        request,
        "error.html",
        status=404,
        context={
            "error_code": "404",
            "error_name": "Page not found",
            "error_message": "Please check the URL in the address bar.",
        },
    )


def permission_denied(request, exception=None):
    return TemplateResponse(
        request,
        "error.html",
        status=403,
        context={
            "error_code": "403",
            "error_name": "Permission denied",
            "error_message": "You do not have permission to access this page.",
        },
    )


def server_error(request):
    return TemplateResponse(
        request,
        "error.html",
        status=500,
        context={
            "error_code": "500",
            "error_name": "Server error",
            "error_message": "An error has occurred displaying this page.",
        },
    )
