from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse

from jobserver.authorization import has_permission

from .form_specs import form_specs
from .models import Application
from .wizard import Wizard


def validate_application_access(user, application):
    if has_permission(user, "application_manage"):
        return

    if application.created_by == user:
        return

    raise Http404


@login_required
def page(request, pk, page_num):
    application = get_object_or_404(Application, pk=pk)

    # check the user can access this application
    validate_application_access(request.user, application)

    page = Wizard(application, form_specs).get_page(page_num)

    if request.method == "GET":
        form = page.get_unbound_form()
    else:
        form = page.get_bound_form(request.POST)
        if form.is_valid():
            if application.has_reached_confirmation:
                return redirect("applications:confirmation", pk=application.pk)
            return page.redirect_to_next_page()

    ctx = page.template_context(form)
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
    return redirect("applications:page", pk=application.pk, page_num=1)


@login_required
def confirmation(request, pk):
    application = get_object_or_404(Application, pk=pk)

    # check the user can access this application
    validate_application_access(request.user, application)

    if not application.has_reached_confirmation:
        application.has_reached_confirmation = True
        application.save()

    wizard = Wizard(application, form_specs)
    pages = list(wizard.get_pages())
    ctx = {
        "application": application,
        "pages": pages,
    }
    return TemplateResponse(request, "applications/confirmation.html", ctx)
