"""Views for SiteAlert instances."""

from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from jobserver.authorization import StaffAreaAdministrator
from jobserver.authorization.decorators import require_role
from jobserver.models import SiteAlert
from staff.forms import SiteAlertForm


class SetUserMixin:
    """Update which user updated or created the instance."""

    def form_valid(self, form):
        if not self.object:  # Creation
            form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class GetSuccessURLMixin:
    """Get a success URL to edit the same object we just touched."""

    def get_success_url(self):
        # Use this method rather than success_url as we pass kwargs.
        return reverse("staff:site-alerts:edit", kwargs={"pk": self.object.pk})


@method_decorator(require_role(StaffAreaAdministrator), name="dispatch")
class SiteAlertList(ListView):
    """List all of the SiteAlert instances."""

    model = SiteAlert
    context_object_name = "alerts"
    template_name = "staff/site_alerts/list.html"


@method_decorator(require_role(StaffAreaAdministrator), name="dispatch")
class SiteAlertCreate(
    SuccessMessageMixin, SetUserMixin, GetSuccessURLMixin, CreateView
):
    """Create a new SiteAlert instance."""

    model = SiteAlert
    form_class = SiteAlertForm
    template_name = "staff/site_alerts/form.html"
    success_message = "Alert was created successfully"


@method_decorator(require_role(StaffAreaAdministrator), name="dispatch")
class SiteAlertUpdate(
    SuccessMessageMixin, SetUserMixin, GetSuccessURLMixin, UpdateView
):
    """Update an existing SiteAlert instance."""

    model = SiteAlert
    form_class = SiteAlertForm
    template_name = "staff/site_alerts/form.html"
    success_message = "Alert was updated successfully"


@method_decorator(require_role(StaffAreaAdministrator), name="dispatch")
class SiteAlertDelete(SuccessMessageMixin, DeleteView):
    """Delete an existing SiteAlert instance."""

    model = SiteAlert
    template_name = "staff/site_alerts/delete.html"
    success_url = reverse_lazy("staff:site-alerts:list")
    success_message = "Alert was deleted successfully"
