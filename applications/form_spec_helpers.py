from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass

from django.db.models import Model

from applications.models import Application

from .utils import value_for_presentation


@dataclass
class Form:
    key: str
    model: type(Model)
    title: str
    sub_title: str
    rubric: str
    fieldsets: list[Fieldset]
    footer: str = ""
    can_continue: Callable[[Application], bool] = lambda application: True
    cant_continue_message: str | None = None
    prerequisite: Callable[[Application], bool] = lambda application: True
    template_name: str | None = None

    def form_context(self, form):
        return {
            "title": self.title,
            "sub_title": self.sub_title,
            "rubric": self.rubric,
            "footer": self.footer,
            "non_field_errors": form.non_field_errors(),
            "fieldsets": [fieldset.form_context(form) for fieldset in self.fieldsets],
            "template_name": self.template_name,
        }

    def is_valid(self, page_instance):
        return all(fieldset.is_valid(page_instance) for fieldset in self.fieldsets)

    def review_context(self, page_instance):
        return {
            "title": self.title,
            "sub_title": self.sub_title,
            "fieldsets": [
                fieldset.review_context(page_instance) for fieldset in self.fieldsets
            ],
        }


@dataclass
class Fieldset:
    label: str
    fields: list[Field]

    def form_context(self, form):
        return {
            "label": self.label,
            "fields": [field_spec.form_context(form) for field_spec in self.fields],
        }

    def is_valid(self, page_instance):
        return all(field.is_valid(page_instance) for field in self.fields)

    def review_context(self, page_instance):
        return {
            "label": self.label,
            "fields": [
                field_spec.review_context(page_instance) for field_spec in self.fields
            ],
        }


@dataclass
class Field:
    name: str
    label: str
    help_text: str = ""
    template_name: str | None = None
    attributes: Attributes | None = None
    optional: bool = False

    def form_context(self, form):
        template_lut = {
            "BooleanField": "form_checkbox",
            "CharField": "form_input",
            "YesNoField": "form_radio",
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

        bound_field.help_text = self.help_text

        # render the field component
        context = {
            "field": bound_field,
            "label": self.label,
            "name": self.name,
            "template_name": template_name,
            "required": not self.optional,
        }

        if self.attributes:
            context |= {"attributes": self.attributes.form_context()}

        return context

    def review_context(self, page_instance):
        value = value_for_presentation(self.value(page_instance))
        return {
            "label": self.label,
            "value": value,
            "is_valid": self.is_valid(page_instance),
        }

    def is_valid(self, page_instance):
        if self.optional:
            return True

        value = self.value(page_instance)
        return value not in [None, ""]

    def value(self, page_instance):
        return getattr(page_instance, self.name)


@dataclass
class Attributes:
    type: str = "text"  # noqa: A003
    inputmode: str | None = None
    autocomplete: str | None = None
    autocapitalize: str | None = None
    spellcheck: str | None = None
    autocorrect: str | None = None
    maxlength: str | None = None

    def form_context(self):
        return {k: v for k, v in asdict(self).items() if v is not None}
