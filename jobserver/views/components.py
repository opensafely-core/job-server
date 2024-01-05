from datetime import UTC, datetime

from django.template.response import TemplateResponse


def components(request):
    example_date = datetime.fromtimestamp(1667317153, tz=UTC)
    example_form_email = {
        "auto_id": "id_email",
        "errors": {"This email is registered to a different account"},
        "html_name": "email",
        "id_for_label": "id_email",
        "label": "Email address",
        "value": "you@example.com",
    }

    example_form_select = {
        "auto_id": "id_language_select",
        "choices": [
            ["", "Please select a language"],
            ["english", "English"],
            ["french", "French"],
            ["german", "German"],
            ["spanish", "Spanish"],
        ],
        "errors": {},
        "html_name": "language-select",
        "id_for_label": "id_language_select",
        "label": "Language select",
        "value": "french",
    }

    example_form_textarea = {
        "auto_id": "id_project_description",
        "errors": {},
        "html_name": "project-description",
        "id_for_label": "id_project_description",
        "label": "Notification email address",
        "value": "",
    }

    return TemplateResponse(
        request,
        "_components/index.html",
        context={
            "example_date": example_date,
            "example_form_email": example_form_email,
            "example_form_select": example_form_select,
            "example_form_textarea": example_form_textarea,
        },
    )
