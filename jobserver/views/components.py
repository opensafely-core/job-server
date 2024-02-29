from datetime import UTC, datetime

from django import forms
from django.template.response import TemplateResponse


class ExampleForm(forms.Form):

    example_select = forms.ChoiceField(
        choices=[
            ["", "Please select a language"],
            ["english", "English"],
            ["french", "French"],
            ["german", "German"],
            ["spanish", "Spanish"],
        ],
        label="Language select",
        initial="french",
    )

    example_email = forms.EmailField()

    example_textarea = forms.Textarea()

    example_radios = forms.ChoiceField(
        choices=[
            ["english", "English"],
            ["french", "French"],
            ["german", "German"],
            ["spanish", "Spanish"],
        ],
        label="Language select",
        initial="french",
        widget=forms.RadioSelect,
    )

    def clean_example_email(self):
        self.add_error(
            "example_email", "This email is registered to a different account"
        )


def components(request):
    example_date = datetime.fromtimestamp(1667317153, tz=UTC)
    form = ExampleForm({"example_select": "french", "example_email": "you@example.com"})
    form.is_valid()
    return TemplateResponse(
        request,
        "_components/index.html",
        context={
            "example_date": example_date,
            "example_form": form,
        },
    )
