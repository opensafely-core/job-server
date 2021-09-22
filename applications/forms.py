from django import forms
from django.template.loader import render_to_string


class ApplicationFormBase(forms.ModelForm):
    """
    A base ModelForm for use with modelform_factory

    This provides the `as_html` method to mirror Form's .as_p(), etc methods,
    but using our own templates and components.
    """

    def as_html(self):
        return render_to_string(
            "applications/process_form.html", context=self.spec.template_context(self)
        )
