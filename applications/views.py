from django.forms.models import modelform_factory
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import CreateView, DetailView, UpdateView

# from . import forms as application_forms
from .forms import Form1
from .models import Application


application_forms = {
    2: [
        "study_name",
        "purpose",
    ],
    3: [
        "purpose",
        "author_name",
        "author_email",
        "author_organisation",
    ],
    4: [
        "study_data",
        "need_record_level_data",
    ],
    5: [
        "record_level_data_reasons",
    ],
    6: [
        "is_study_research",
        "is_study_a_service_evaluation",
    ],
    7: [
        "hra_ires_id",
        "hra_rec_reference",
        "institutional_rec_reference",
    ],
    8: [
        "institutional_rec_reference",
    ],
    9: [
        "is_on_cmo_priority_list",
    ],
    10: [
        "funding_details",
    ],
    11: [
        "team_details",
    ],
    12: [
        "previous_experience_with_ehr",
    ],
    13: [
        "evidence_of_coding",
    ],
    14: [
        "evidence_of_sharing_in_public_domain_before",
    ],
    15: [
        "number_of_researchers_needing_access",
    ],
    16: [
        "has_agreed_to_terms",
    ],
}


def application(request):
    return render(request, "application.html")


class ApplicationProcess(UpdateView):
    model = Application
    template_name = "applications/application_process_page.html"

    def get_form_class(self):
        page_num = self.kwargs["page_num"]
        fields = application_forms[page_num]
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
