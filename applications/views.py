from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, RedirectView, UpdateView, View

from jobserver.authorization import CoreDeveloper, has_permission, has_role
from jobserver.hash_utils import unhash_or_404
from jobserver.slacks import notify_application

from .emails import send_submitted_application_email
from .form_specs import form_specs
from .forms import ResearcherRegistrationPageForm
from .models import Application, ResearcherRegistration
from .researchers import build_researcher_form
from .wizard import Wizard


def validate_application_access(user, application):
    if has_permission(user, "application_manage"):
        return

    if application.created_by == user:
        return

    raise Http404


def get_next_url(get_args):
    try:
        return get_args["next"]
    except KeyError:
        return reverse("applications:list")


@method_decorator(login_required, name="dispatch")
class ApplicationList(View):
    def get(self, request, *args, **kwargs):
        applications = Application.objects.filter(created_by=self.request.user)

        context = {
            "applications": applications.filter(deleted_at=None),
            "deleted_applications": applications.exclude(deleted_at=None),
        }

        return TemplateResponse(request, "applications/application_list.html", context)


@method_decorator(login_required, name="dispatch")
class ApplicationRemove(View):
    def post(self, request, *args, **kwargs):
        application = get_object_or_404(
            Application,
            pk=unhash_or_404(self.kwargs["pk_hash"]),
        )

        if application.created_by != request.user:
            raise Http404

        if application.is_approved:
            messages.error(request, "You cannot delete an approved Application.")
            return redirect("applications:list")

        if application.is_deleted:
            messages.error(
                request, f"Application {application.pk_hash} has already been deleted"
            )
            return redirect("applications:list")

        application.deleted_at = timezone.now()
        application.deleted_by = request.user
        application.save()

        return redirect("applications:list")


@method_decorator(login_required, name="dispatch")
class ApplicationRestore(View):
    def post(self, request, *args, **kwargs):
        application = get_object_or_404(
            Application,
            pk=unhash_or_404(self.kwargs["pk_hash"]),
        )

        if application.created_by != request.user:
            raise Http404

        if application.is_deleted:
            application.deleted_at = None
            application.deleted_by = None
            application.save()

        return redirect("applications:list")


class PageRedirect(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse(
            "applications:page",
            kwargs={
                "pk_hash": self.kwargs["pk_hash"],
                "key": form_specs[0].key,
            },
        )


class ResearcherCreate(CreateView):
    form_class = ResearcherRegistrationPageForm
    model = ResearcherRegistration
    template_name = "applications/researcher_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.application = get_object_or_404(
            Application, pk=unhash_or_404(self.kwargs["pk_hash"])
        )

        validate_application_access(request.user, self.application)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        researcher = form.save(commit=False)
        researcher.application = self.application
        researcher.save()

        return redirect(get_next_url(self.request.GET))


class ResearcherDelete(View):
    def post(self, request, *args, **kwargs):
        researcher = get_object_or_404(
            ResearcherRegistration,
            application__pk=unhash_or_404(self.kwargs["pk_hash"]),
            pk=self.kwargs["researcher_pk"],
        )

        validate_application_access(request.user, researcher.application)

        researcher.delete()

        messages.success(
            request,
            f'Successfully removed researcher "{researcher.email}" from application',
        )

        return redirect(get_next_url(request.GET))


class ResearcherEdit(UpdateView):
    form_class = ResearcherRegistrationPageForm
    model = ResearcherRegistration
    template_name = "applications/researcher_form.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "is_edit": True,
        }

    def get_object(self, queryset=None):
        researcher = get_object_or_404(
            ResearcherRegistration,
            application__pk=unhash_or_404(self.kwargs["pk_hash"]),
            pk=self.kwargs["researcher_pk"],
        )

        validate_application_access(self.request.user, researcher.application)

        return researcher

    def get_success_url(self):
        return get_next_url(self.request.GET)


@login_required
def page(request, pk_hash, key):
    application = get_object_or_404(Application, pk=unhash_or_404(pk_hash))

    if application.is_deleted:
        msg = f"Application {application.pk_hash} has been deleted, you need to restore it before you can view it."
        messages.error(request, msg)
        return redirect("applications:list")

    # check the user can access this application
    validate_application_access(request.user, application)

    if application.approved_at and not has_role(request.user, CoreDeveloper):
        messages.warning(
            request, "This application has been approved and can no longer be edited"
        )
        return redirect("applications:confirmation", pk_hash=application.pk_hash)

    try:
        wizard_page = Wizard(application, form_specs).get_page(key)
    except ValueError:
        raise Http404

    if request.method == "GET":
        form = wizard_page.get_unbound_data_form()
    else:
        form = wizard_page.get_bound_data_form(request.POST)

        if form.has_changed():
            wizard_page.page_instance.is_approved = False
            wizard_page.page_instance.save()

        form.save()
        if not wizard_page.form_spec.can_continue(application):
            form.add_error(None, wizard_page.form_spec.cant_continue_message)

        if form.is_valid():
            return wizard_page.redirect_to_next_page()

    ctx = wizard_page.form_context(form)
    return TemplateResponse(request, "applications/page.html", ctx)


def sign_in(request):
    if not request.user.is_authenticated:
        return TemplateResponse(request, "applications/sign_in.html")

    return redirect("applications:terms")


@login_required
def terms(request):
    if request.method == "GET":
        return TemplateResponse(request, "applications/terms.html")

    application = Application.objects.create(created_by=request.user)

    notify_application(application, request.user, "New application started")

    return redirect(
        "applications:page", pk_hash=application.pk_hash, key=form_specs[0].key
    )


@method_decorator(login_required, name="dispatch")
class Confirmation(View):
    def dispatch(self, request, *args, **kwargs):
        application = get_object_or_404(
            Application, pk=unhash_or_404(self.kwargs["pk_hash"])
        )
        self.application = application

        # check the user can access this application
        validate_application_access(request.user, application)

        self.wizard = Wizard(application, form_specs)

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        pages = [page.review_context() for page in self.wizard.get_pages()]

        researchers = [
            build_researcher_form(r)
            for r in self.application.researcher_registrations.order_by("name")
        ]
        context = {
            "application": self.application,
            "is_valid": self.wizard.is_valid(),
            "can_be_submitted": self.application.status == Application.Statuses.ONGOING,
            "pages": pages,
            "researchers": researchers,
        }

        return TemplateResponse(
            request,
            "applications/confirmation.html",
            context=context,
        )

    def post(self, request, *args, **kwargs):
        if not self.wizard.is_valid():
            return self.get(request, *args, **kwargs)

        self.application.submitted_at = timezone.now()
        self.application.submitted_by = self.request.user
        self.application.status = Application.Statuses.SUBMITTED
        self.application.save()

        notify_application(self.application, request.user, "Application submitted")

        send_submitted_application_email(request.user.email, self.application)

        messages.success(request, "Application submitted")
        return redirect("applications:list")
