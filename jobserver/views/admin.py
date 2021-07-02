from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import FormView

from ..models import Backend, BackendMembership, Org, OrgMembership, User


class ApprovalForm(forms.Form):
    def __init__(self, backends, orgs, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # bulid the backends and orgs fields based on the values passed in
        self.fields["backends"] = forms.ModelMultipleChoiceField(queryset=backends)
        self.fields["orgs"] = forms.ModelMultipleChoiceField(queryset=orgs)


@method_decorator(user_passes_test(lambda u: u.is_superuser), name="dispatch")
class ApproveUsers(FormView):
    form_class = ApprovalForm
    success_url = reverse_lazy("admin:jobserver_user_changelist")
    template_name = "approve_users.html"

    def dispatch(self, request, *args, **kwargs):
        pks = self.request.GET.getlist("user")

        if not pks:
            messages.error(request, "One or more users must be selected")
            return redirect(self.success_url)

        self.users = User.objects.filter(pk__in=pks)

        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic()
    def form_valid(self, form):
        backends = form.cleaned_data["backends"]
        orgs = form.cleaned_data["orgs"]

        for user in self.users:
            for backend in backends:
                BackendMembership.objects.get_or_create(backend=backend, user=user)

            for org in orgs:
                OrgMembership.objects.get_or_create(org=org, user=user)

        messages.info(self.request, "Connected Users to selected Backends & Orgs")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            users=self.users,
            **kwargs,
        )

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {
            "backends": Backend.objects.order_by("name"),
            "orgs": Org.objects.order_by("name"),
        }
