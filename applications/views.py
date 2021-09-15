from django.forms.models import modelform_factory
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import CreateView, DetailView, UpdateView

from .form_specs import form_specs
from .forms import Form1
from .models import Application


def application(request):
    return render(request, "application.html")


class ApplicationProcess(UpdateView):
    model = Application
    template_name = "applications/application_process_page.html"

    def get_form_class(self):
        page_num = self.kwargs["page_num"]
        form_spec = form_specs[page_num]
        fields = []
        for fieldset in form_spec["fieldsets"]:
            for field in fieldset["fields"]:
                fields.append(field["name"])
        return modelform_factory(self.model, fields=fields)

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
