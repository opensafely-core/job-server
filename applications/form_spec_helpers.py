from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from applications.models import Application
from jobserver.snippets import render_snippet


SNIPPET = "<snippet>"


@dataclass
class Form:
    key: int
    title: str
    sub_title: str
    rubric: str
    fieldsets: list[Fieldset]
    footer: str = ""
    can_continue: Callable[[Application], bool] = lambda application: True
    cant_continue_message: str | None = None
    prerequisite: Callable[[Application], bool] = lambda application: True
    template_name: str | None = None

    def __post_init__(self):
        for fieldset_ix, fieldset in enumerate(self.fieldsets):
            fieldset.key = f"{self.key}-fieldset{fieldset_ix}"

            for field_ix, field in enumerate(fieldset.fields):
                field.key = f"{self.key}-fieldset{fieldset_ix}-field{field_ix}"

    def template_context(self, form):
        rubric = maybe_replace_value_with_snippet(self.rubric, f"{self.key}-rubric")
        footer = maybe_replace_value_with_snippet(self.footer, f"{self.key}-footer")

        return {
            "title": self.title,
            "sub_title": self.sub_title,
            "rubric": rubric,
            "footer": footer,
            "non_field_errors": form.non_field_errors(),
            "fieldsets": [
                fieldset.template_context(form) for fieldset in self.fieldsets
            ],
            "template_name": self.template_name,
        }


@dataclass
class Fieldset:
    label: str
    fields: list[Field]

    def template_context(self, form):
        label = maybe_replace_value_with_snippet(self.label, f"{self.key}-label")

        return {
            "label": label,
            "fields": [field_spec.template_context(form) for field_spec in self.fields],
        }


@dataclass
class Field:
    name: str
    label: str
    help_text: str = ""
    template_name: str | None = None

    def template_context(self, form):
        template_lut = {
            "BooleanField": "components/form_checkbox.html",
            "CharField": "components/form_text.html",
            "TypedChoiceField": "components/form_radio.html",
        }

        # get the bound field instance
        # Note: doing this with form.fields gets the plain field instance
        bound_field = form[self.name]

        if self.template_name is not None:
            template_name = self.template_name
        else:
            # fall back to getting the component template using the field class
            # name
            # Note: this is original field class, not the bound version
            template_name = template_lut[bound_field.field.__class__.__name__]

        label = maybe_replace_value_with_snippet(self.label, f"{self.key}-label")
        bound_field.help_text = maybe_replace_value_with_snippet(
            self.help_text, f"{self.key}-help_text"
        )

        # render the field component
        context = {
            "field": bound_field,
            "label": label,
            "name": self.name,
            "template_name": template_name,
        }

        return context


def maybe_replace_value_with_snippet(value, key):
    if value == SNIPPET:
        return render_snippet(key)
    else:
        return value
