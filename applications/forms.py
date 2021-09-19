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
            "IntegerField": "components/form_number.html",
            "TypedChoiceField": "components/form_radio.html",
        }

        # attach the rendered component to each field
        for i, fieldset_spec in enumerate(self.spec["fieldsets"]):
            for j, field_spec in enumerate(fieldset_spec["fields"]):
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
                rendered_field = render_to_string(template_name, context)

                # mutate the spec on this ModelForm instance so we can use it
                # in the context below
                self.spec["fieldsets"][i]["fields"][j]["rendered"] = rendered_field

        # this is definitely not the right place to put this, but it works for now
        self.spec["non_field_errors"] = self.non_field_errors()

        return render_to_string("applications/process_form.html", context=self.spec)
