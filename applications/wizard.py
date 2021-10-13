from django.forms.models import modelform_factory
from django.shortcuts import redirect
from django.utils.functional import cached_property

from .forms import PageFormBase


UNSTARTED = "unstarted"
NEEDS_REVIEW = "needs review"
NOT_APPROVED = "not approved"
APPROVED = "approved"


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
            if not form_spec.prerequisite(self.application):
                continue
            page = WizardPage(self, form_spec)
            if page.status == UNSTARTED:
                return page.key

    def progress_percent(self):
        """Return user's progress through wizard as a percentage."""

        pages = list(self.get_pages())
        num_pages = len(pages)
        num_pages_done = len([p for p in pages if p.status != UNSTARTED])

        return int(100 * num_pages_done / num_pages)


class WizardPage:
    def __init__(self, wizard, form_spec):
        self.wizard = wizard
        self.application = wizard.application
        self.form_spec = form_spec
        self.model = form_spec.model

    @property
    def data_form_class(self):
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

        return modelform_factory(self.model, fields=fields, form=PageFormBase)

    @property
    def approval_form_class(self):
        fields = ["notes", "is_approved"]
        return modelform_factory(self.model, fields=fields, form=PageFormBase)

    @cached_property
    def page_instance(self):
        """
        Return instance of model containing data for this page.

        If this page has already been saved, there will be an instance in the
        database and we return that.  Otherwise, we return a new unsaved instance.
        """
        try:
            return self.model.objects.get(application=self.application)
        except self.model.DoesNotExist:
            return self.model(application=self.application)

    @property
    def status(self):
        if not self.page_instance.pk:
            return UNSTARTED

        return {
            None: NEEDS_REVIEW,
            True: APPROVED,
            False: NOT_APPROVED,
        }[self.page_instance.is_approved]

    def get_unbound_data_form(self):
        """
        Create a form instance without POST data (typically for GET requests)
        """
        return self.data_form_class(instance=self.page_instance)

    def get_unbound_approval_form(self):
        return self.approval_form_class(instance=self.page_instance)

    def get_bound_data_form(self, data):
        """
        Create a form instance with POST data
        """
        return self.data_form_class(data, instance=self.page_instance)

    def get_bound_approval_form(self, data):
        return self.approval_form_class(
            data, instance=self.page_instance, prefix=self.key
        )

    @property
    def key(self):
        return self.form_spec.key

    @property
    def notes_field_name(self):
        return f"{self.key}-notes"

    @property
    def is_approved_field_name(self):
        return f"{self.key}-is_approved"

    def form_context(self, form):
        return self.form_spec.form_context(form) | {
            "application": self.application,
            "page": self,
            "progress_percent": self.wizard.progress_percent(),
        }

    def review_context(self):
        return self.form_spec.review_context(self.page_instance) | {
            "key": self.key,
            "started": self.status != UNSTARTED,
            "status": self.status,
            "wizard_page": self,
        }

    def redirect_to_next_page(self):
        if (next_page_key := self.wizard.get_next_page_key(self.key)) is None:
            return redirect("applications:confirmation", pk=self.application.pk)
        else:
            return redirect(
                "applications:page", pk=self.application.pk, key=next_page_key
            )
