from django.forms.models import modelform_factory

from jobserver.snippets import expand_snippets

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
        return expand_snippets(self.form_specs[page_num - 1])

    def is_page_required(self, page_num):
        form_spec = self.get_form_spec(page_num)
        prerequisite = form_spec["prerequisite"]
        return prerequisite(self.application)


class WizardPage:
    def __init__(self, wizard, page_num):
        self.wizard = wizard
        self.form_spec = wizard.get_form_spec(page_num)
        self.application = wizard.application
        self.page_num = page_num

    @property
    def form_class(self):
        fields = []
        for fieldset in self.form_spec["fieldsets"]:
            for field in fieldset["fields"]:
                fields.append(field["name"])
        form_class = modelform_factory(
            Application, form=ApplicationFormBase, fields=fields
        )

        # attach the spec for this particular form so we can use it for
        # presentation in the template too
        form_class.spec = self.form_spec

        return form_class

    def get_unbound_form(self):
        return self.form_class(instance=self.application)

    def get_bound_form(self, data):
        return self.form_class(data, instance=self.application)

    def validate_form(self, form):
        can_continue = self.form_spec["can_continue"]
        if not can_continue(self.application):
            form.add_error(None, self.form_spec["cant_continue_message"])

    @property
    def title(self):
        return self.form_spec["title"]

    @property
    def next_page_num(self):
        next_page_num = self.page_num + 1
        while next_page_num <= len(self.wizard.form_specs):
            if self.wizard.is_page_required(next_page_num):
                return next_page_num
            next_page_num += 1
        return None
