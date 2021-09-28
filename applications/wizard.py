from django.forms.models import modelform_factory
from django.shortcuts import redirect

from .forms import ApplicationFormBase
from .models import Application


class Wizard:
    def __init__(self, application, form_specs):
        self.application = application
        self.form_specs = form_specs

    def get_pages(self):
        for page_num in range(1, len(self.form_specs) + 1):
            if self.is_page_required(page_num):
                yield self.get_page(page_num)

    def get_page(self, page_num):
        return WizardPage(self, page_num)

    def get_form_spec(self, page_num):
        return self.form_specs[page_num - 1]

    def is_page_required(self, page_num):
        form_spec = self.get_form_spec(page_num)
        prerequisite = form_spec.prerequisite
        return prerequisite(self.application)


class WizardPage:
    def __init__(self, wizard, page_num):
        self.wizard = wizard
        self.form_spec = wizard.get_form_spec(page_num)
        self.application = wizard.application
        self.page_num = page_num

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
            Application, fields=fields, form=ApplicationFormBase
        )

        return form_class

    def get_unbound_form(self):
        """
        Create a form instance without POST data (typically for GET requests)
        """
        return self.form_class(instance=self.application)

    def get_bound_form(self, data):
        """
        Create a form instance with POST data

        When a page is submitted we validate the submitted data and check if
        the user can continue to the next page based on rules defined in the
        form_spec for this page.
        """
        form = self.form_class(data, instance=self.application)
        form.save()

        if not self.form_spec.can_continue(self.application):
            form.add_error(None, self.form_spec.cant_continue_message)

        return form

    @property
    def title(self):
        return self.form_spec.title

    @property
    def next_page_num(self):
        next_page_num = self.page_num + 1
        while next_page_num <= len(self.wizard.form_specs):
            if self.wizard.is_page_required(next_page_num):
                return next_page_num
            next_page_num += 1
        return None

    def template_context(self, form):
        return self.form_spec.template_context(form) | {
            "application": self.application,
            "page": self,
        }

    def redirect_to_next_page(self):
        if (next_page_num := self.next_page_num) is None:
            return redirect("applications:confirmation", pk=self.application.pk)
        else:
            return redirect(
                "applications:page", pk=self.application.pk, page_num=next_page_num
            )
