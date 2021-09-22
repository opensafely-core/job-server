from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from applications.models import Application


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

    def template_context(self, form):
        return {
            "title": self.title,
            "sub_title": self.sub_title,
            "rubric": self.rubric,
            "footer": self.footer,
            "non_field_errors": form.non_field_errors(),
            "fieldsets": [
                fieldset.template_context(form) for fieldset in self.fieldsets
            ],
        }


@dataclass
class Fieldset:
    label: str
    fields: list[Field]

    def template_context(self, form):
        return {
            "label": self.label,
            "fields": [field_spec.template_context(form) for field_spec in self.fields],
        }


@dataclass
class Field:
    name: str
    label: str
    help_text: str = ""

    def template_context(self, form):
        template_lut = {
            "BooleanField": "components/form_checkbox.html",
            "CharField": "components/form_text.html",
            "TypedChoiceField": "components/form_radio.html",
        }

        # get the bound field instance
        # Note: doing this with form.fields gets the plain field instance
        bound_field = form[self.name]

        # get the component template using the field class name
        # Note: this is original field class, not the bound version
        template_name = template_lut[bound_field.field.__class__.__name__]

        # render the field component
        context = {
            "field": bound_field,
            "label": self.label,
            "name": self.name,
            "template_name": template_name,
        }

        return context
