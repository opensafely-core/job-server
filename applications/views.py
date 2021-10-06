from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.generic import CreateView, ListView, RedirectView, UpdateView, View

from jobserver.authorization import has_permission

from .form_specs import form_specs
from .forms import ResearcherRegistrationForm
from .models import Application, ResearcherRegistration
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
    form_class = ResearcherRegistrationForm
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
    form_class = ResearcherRegistrationForm
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
        page = Wizard(application, form_specs).get_page(key)
    except ValueError:
        raise Http404

    if request.method == "GET":
        form = page.get_unbound_data_form()
    else:
        form = page.get_bound_data_form(request.POST)

        if form.has_changed():
            page.instance.is_approved = False
            page.instance.save()

        form.save()
        if not page.form_spec.can_continue(application):
            form.add_error(None, page.form_spec.cant_continue_message)

        if form.is_valid():
            return page.redirect_to_next_page()

    ctx = page.form_context(form)
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
    return redirect("applications:page", pk=application.pk, key=form_specs[0].key)


@login_required
def confirmation(request, pk):
    application = get_object_or_404(Application, pk=pk)

    # check the user can access this application
    validate_application_access(request.user, application)

    wizard = Wizard(application, form_specs)
    pages = list(wizard.get_pages())
    ctx = {
        "application": application,
        "pages": pages,
    }
    return TemplateResponse(request, "applications/confirmation.html", ctx)
