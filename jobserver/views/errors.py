from textwrap import dedent

from django.core.exceptions import TooManyFieldsSent
from django.template.response import TemplateResponse
from markdown import markdown

from jobserver import html_utils


def markdown_error_message(error_message):
    return html_utils.clean_html(markdown(dedent(error_message).strip()))


def bad_request(request, exception=None):
    if isinstance(exception, TooManyFieldsSent):
        return TemplateResponse(
            request,
            "error.html",
            status=413,
            context={
                "error_code": "413",
                "error_name": "Too many fields submitted",
                "error_message": markdown_error_message(
                    "Your submission contained too many fields. Please reduce the number of selected items and try again."
                ),
            },
        )

    return TemplateResponse(
        request,
        "error.html",
        status=400,
        context={
            "error_code": "400",
            "error_name": "Bad request",
            "error_message": markdown_error_message(
                "An error occurred while displaying this page."
            ),
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
            "error_message": markdown_error_message("The form could not be submitted."),
        },
    )


def page_not_found(request, exception=None):

    if not request.user.is_authenticated:
        error_message = """
            We could not find the page you are looking for.

            This may be because:

            - the link is incorrect
            - the page has moved
            - you need to log in to view this page

            Please check the URL, try logging in, or contact us if you need further help.
        """

    else:
        error_message = """
            We could not find the page you are looking for.

            This may be because:

            - the link is incorrect
            - the page has moved

            Please check the URL or contact us if you need further help.
        """

    return TemplateResponse(
        request,
        "error.html",
        status=404,
        context={
            "error_code": "404",
            "error_name": "Page not found",
            "error_message": markdown_error_message(error_message),
        },
    )


def permission_denied(request, exception=None):

    if not request.user.is_authenticated:
        error_message = """
            You do not have permission to access this page.

            This may be because:

            - you need to log in to view this page
            - your account does not have the required permissions

            Try logging in, or contact us if you need to discuss permissions.
        """
    else:
        error_message = "You do not have permission to access this page. Contact us if you have a question about your permissions or need further support."

    return TemplateResponse(
        request,
        "error.html",
        status=403,
        context={
            "error_code": "403",
            "error_name": "Permission denied",
            "error_message": markdown_error_message(error_message),
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
            "error_message": markdown_error_message(
                "An error occurred while displaying this page."
            ),
        },
    )
