from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView

from applications.models import ResearcherRegistration
from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role
from jobserver.hash_utils import unhash_or_404

from ..forms import ResearcherRegistrationEditForm


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ResearcherEdit(UpdateView):
    context_object_name = "researcher"
    form_class = ResearcherRegistrationEditForm
    template_name = "staff/application/researcher_edit.html"

    def get_object(self, queryset=None):
        application_pk = unhash_or_404(self.kwargs["pk_hash"])

        return get_object_or_404(
            ResearcherRegistration, application__pk=application_pk, pk=self.kwargs["pk"]
        )

    def get_success_url(self):
        return self.object.application.get_staff_url()
