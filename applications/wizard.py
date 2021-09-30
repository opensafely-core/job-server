from django.forms.models import modelform_factory
from django.shortcuts import redirect

from .forms import ApplicationFormBase


class Wizard:
    def __init__(self, application, form_specs):
        self.application = application
        self.form_specs = form_specs
        self.keys = [form_spec.key for form_spec in form_specs]

    def get_page(self, key):
        form_spec = self.form_specs[self.keys.index(key)]
        return WizardPage(self, form_spec)

    def get_pages(self):
        for form_spec in self.form_specs:
            if form_spec.prerequisite(self.application):
                yield WizardPage(self, form_spec)

    def get_next_page_key(self, key):
        next_ix = self.keys.index(key) + 1

        for form_spec in self.form_specs[next_ix:]:
            if form_spec.prerequisite(self.application):
                return form_spec.key


class WizardPage:
    def __init__(self, wizard, form_spec):
        self.wizard = wizard
        self.application = wizard.application
        self.form_spec = form_spec
        self.model = form_spec.model

    @property
    def form_class(self):
        """
        Construct a ModelForm class from this page's form_spec

        Each page uses a ModelForm instance which we dynamically construct with
        Django's modelform_factory, using the fields defined by the fieldsets
        of a given form_spec.
        """
        fields = []
        for fieldset in self.form_spec.fieldsets:
            for field in fieldset.fields:
                fields.append(field.name)
        form_class = modelform_factory(
            self.model, fields=fields, form=ApplicationFormBase
        )

        return form_class

    @property
    def instance(self):
        """
        Return instance of model containing data for this page.

        If this page has already been saved, there will be an instance in the
        database and we return that.  Otherwise, we return a new unsaved instance.
        """
        try:
            return self.model.objects.get(application=self.application)
        except self.model.DoesNotExist:
            return self.model(application=self.application)

    def get_unbound_form(self):
        """
        Create a form instance without POST data (typically for GET requests)
        """
        return self.form_class(instance=self.instance)

    def get_bound_form(self, data):
        """
        Create a form instance with POST data

        When a page is submitted we validate the submitted data and check if
        the user can continue to the next page based on rules defined in the
        form_spec for this page.
        """
        form = self.form_class(data, instance=self.instance)
        form.save()

        if not self.form_spec.can_continue(self.application):
            form.add_error(None, self.form_spec.cant_continue_message)

        return form

    @property
    def title(self):
        return self.form_spec.title

    @property
    def key(self):
        return self.form_spec.key

    def template_context(self, form):
        return self.form_spec.template_context(form) | {
            "application": self.application,
            "page": self,
        }

    def redirect_to_next_page(self):
        if (next_page_key := self.wizard.get_next_page_key(self.key)) is None:
            return redirect("applications:confirmation", pk=self.application.pk)
        else:
            return redirect(
                "applications:page", pk=self.application.pk, key=next_page_key
            )
