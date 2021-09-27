from django import forms

from applications.form_spec_helpers import Field


def test_field_template_context_template_name_override():
    class Form(forms.Form):
        field_name = forms.CharField()

    field = Field(
        name="field_name",
        label="Field Label",
        template_name="test",
    )
    field.key = 42

    form = Form()

    context = field.template_context(form)

    assert context["template_name"] == "test"
