from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, RedirectView, UpdateView, View
from furl import furl

from jobserver.authorization import has_permission
from services.slack import client as slack_client

from .emails import send_submitted_application_email
from .form_specs import form_specs
from .forms import ResearcherRegistrationPageForm
from .models import Application, ResearcherRegistration
from .researchers import build_researcher_form
from .wizard import Wizard


def notify_slack(application, msg):
    f = furl(settings.BASE_URL)
    f.path = application.get_staff_url()
    slack_client.chat_postMessage(
        channel="job-server-applications",
        text=f"{msg}: {f.url}",
    )


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
class ApplicationList(ListView):
    context_object_name = "applications"
    template_name = "applications/application_list.html"

    def get_queryset(self):
        return Application.objects.filter(created_by=self.request.user)


class PageRedirect(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse(
            "applications:page",
            kwargs={
                "pk": self.kwargs["pk"],
                "key": form_specs[0].key,
            },
        )


class ResearcherCreate(CreateView):
    form_class = ResearcherRegistrationPageForm
    model = ResearcherRegistration
    template_name = "applications/researcher_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.application = get_object_or_404(Application, pk=self.kwargs["pk"])

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
            application__pk=self.kwargs["pk"],
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
            application__pk=self.kwargs["pk"],
            pk=self.kwargs["researcher_pk"],
        )

        validate_application_access(self.request.user, researcher.application)

        return researcher

    def get_success_url(self):
        return get_next_url(self.request.GET)


@login_required
def page(request, pk, key):
    application = get_object_or_404(Application, pk=pk)

    # check the user can access this application
    validate_application_access(request.user, application)

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

    notify_slack(application, "New application started")

    return redirect("applications:page", pk=application.pk, key=form_specs[0].key)


@method_decorator(login_required, name="dispatch")
class Confirmation(View):
    def dispatch(self, request, *args, **kwargs):
        application = get_object_or_404(Application, pk=self.kwargs["pk"])

        # check the user can access this application
        validate_application_access(request.user, application)

        self.wizard = Wizard(application, form_specs)

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        pages = [page.review_context() for page in self.wizard.get_pages()]

        researchers = [
            build_researcher_form(r)
            for r in self.wizard.application.researcher_registrations.order_by("name")
        ]
        context = {
            "application": self.wizard.application,
            "is_valid": self.wizard.is_valid(),
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

        notify_slack(self.wizard.application, "Application submitted")

        send_submitted_application_email(request.user.email, self.wizard.application)

        messages.success(request, "Application submitted")
        return redirect("applications:list")
