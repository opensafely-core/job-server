from django import forms
from django.forms.models import modelform_factory
from django.http import Http404
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import CreateView, DetailView, UpdateView
from first import first

from .form_specs import form_specs
from .forms import Form1
from .models import Application


def application(request):
    return render(request, "application.html")


class ApplicationFormBase(forms.ModelForm):
    """
    A base ModelForm for use with modelform_factory

    This provides the `as_html` method to mirror Form's .as_p(), etc methods,
    but using our own templates and components.
    """

    def as_html(self):
        template_lut = {
            "CharField": "components/form_text.html",
            "IntegerField": "components/form_number.html",
            "NullBooleanField": "components/form_radio.html",
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

        return render_to_string("applications/process_form.html", context=self.spec)


class ApplicationProcess(UpdateView):
    model = Application
    template_name = "applications/application_process_page.html"

    def get_form_class(self):
        page_num = self.kwargs["page_num"]
        form_spec = first(form_specs, key=lambda s: s["key"] == page_num)
        if not form_spec:
            raise Http404

        fields = []
        for fieldset in form_spec["fieldsets"]:
            for field in fieldset["fields"]:
                fields.append(field["name"])

        form_class = modelform_factory(
            self.model, form=ApplicationFormBase, fields=fields
        )

        # attach the spec for this particular form so we can use it for
        # presentation in the template too
        form_class.spec = form_spec

        return form_class

    def get_success_url(self):
        page_num = self.kwargs["page_num"]
        return reverse(
            "applications:application-process",
            kwargs={
                "pk": self.object.pk,
                "page_num": page_num + 1,
            },
        )

    # def get_template_names(self):
    #     page_num = self.kwargs["page_num"]

    #     return f"applications/application_process_page_{page_num}.html"


class ApplicationDetail(DetailView):
    model = Application
    template_name = "applications/application_detail.html"


class Apply(CreateView):
    form_class = Form1
    model = Application
    template_name = "applications/apply.html"

    def get_success_url(self):
        return reverse("application-detail", kwargs={"pk": self.object})
