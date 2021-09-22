from django import forms
from django.template.loader import render_to_string


class ApplicationFormBase(forms.ModelForm):
    """
    A base ModelForm for use with modelform_factory

    This provides the `as_html` method to mirror Form's .as_p(), etc methods,
    but using our own templates and components.
    """

    def as_html(self):
        template_lut = {
            "BooleanField": "components/form_checkbox.html",
            "CharField": "components/form_text.html",
            "TypedChoiceField": "components/form_radio.html",
        }

        fieldset_contexts = []
        for fieldset_spec in self.spec["fieldsets"]:
            rendered_fields = []
            for field_spec in fieldset_spec["fields"]:
                # get the bound field instance
                # Note: doing this with self.fields gets the plain field instance
                bound_field = self[field_spec["name"]]

                # get the component template using the field class name
                # Note: this is original field class, not the bound version
                template_name = template_lut[bound_field.field.__class__.__name__]

                # render the field component
                context = {
                    "field": bound_field,
                    "label": field_spec["label"],
                    "name": field_spec["name"],
                }
                rendered_fields.append(render_to_string(template_name, context))

            fieldset_contexts.append(
                {
                    "label": fieldset_spec["label"],
                    "rendered_fields": rendered_fields,
                }
            )

        form_context = {
            "title": self.spec["title"],
            "sub_title": self.spec["sub_title"],
            "rubric": self.spec["rubric"],
            "footer": self.spec["footer"],
            "non_field_errors": self.non_field_errors(),
            "fieldsets": fieldset_contexts,
        }

        return render_to_string("applications/process_form.html", context=form_context)
