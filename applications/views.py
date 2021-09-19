from django.forms.models import modelform_factory
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import CreateView, DetailView, UpdateView
from first import first

from jobserver.snippets import expand_snippets

from .form_specs import form_specs
from .forms import ApplicationFormBase
from .models import Application


def application(request):
    return render(request, "application.html")


class ApplicationProcess(UpdateView):
    model = Application
    template_name = "applications/application_process_page.html"

    def get_form_class(self):
        page_num = self.kwargs["page_num"]
        form_spec = first(form_specs, key=lambda s: s["key"] == page_num)
        if not form_spec:
            raise Http404

        form_spec = expand_snippets(form_spec)

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
