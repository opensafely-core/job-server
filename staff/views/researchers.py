from django.utils.decorators import method_decorator
from django.views.generic import UpdateView

from applications.models import ResearcherRegistration
from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role

from ..forms import ResearcherRegistrationEditForm


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ResearcherEdit(UpdateView):
    context_object_name = "researcher"
    form_class = ResearcherRegistrationEditForm
    model = ResearcherRegistration
    template_name = "staff/researcher/edit.html"

    def get_success_url(self):
        return self.object.application.get_staff_url()
