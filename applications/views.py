from django.shortcuts import get_object_or_404, redirect, render

from .form_specs import form_specs
from .models import Application
from .wizard import Wizard


def new(request):
    if request.method == "POST":
        application = Application.objects.create()
        return redirect("applications:page", pk=application.pk, page_num=1)
    return render(request, "applications/new.html")


def page(request, pk, page_num):
    application = get_object_or_404(Application, pk=pk)
    page = Wizard(application, form_specs).get_page(page_num)

    if request.method == "POST":
        form = page.get_bound_form(request.POST)
        form.save()

        page.validate_form(form)

        if form.is_valid():
            if request.POST["direction"] == "next":
                next_page_num = page.next_page_num
            else:
                assert request.POST["direction"] == "prev"
                next_page_num = page.prev_page_num
                assert next_page_num is not None

            if next_page_num is None:
                return redirect("applications:confirmation", pk=pk)
            else:
                return redirect("applications:page", pk=pk, page_num=next_page_num)

    else:
        form = page.get_unbound_form()

    ctx = {
        "application": application,
        "form": form,
        "page": page,
    }

    return render(request, "applications/page.html", ctx)


def confirmation(request, pk):
    application = get_object_or_404(Application, pk=pk)
    wizard = Wizard(application, form_specs)
    pages = list(wizard.get_pages())
    ctx = {
        "application": application,
        "pages": pages,
    }
    return render(request, "applications/confirmation.html", ctx)
