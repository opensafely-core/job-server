from django import forms


class ApplicationFormBase(forms.ModelForm):
    """
    A base ModelForm for use with modelform_factory

    This provides the `as_html` method to mirror Form's .as_p(), etc methods,
    but using our own templates and components.
    """

    pass
