import functools

from django.contrib import messages
from django.db.models import Max, Q, Value
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import FormView, ListView, UpdateView, View
from zen_queries import TemplateResponse, fetch

from applications.form_specs import form_specs
from applications.models import Application
from applications.wizard import Wizard
from jobserver.authorization import CoreDeveloper
from jobserver.authorization.decorators import require_role
from jobserver.hash_utils import unhash, unhash_or_404
from jobserver.models import Org, Project, User

from ..forms import ApplicationApproveForm


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ApplicationApprove(FormView):
    form_class = ApplicationApproveForm
    model = Application
    response_class = TemplateResponse
    template_name = "staff/application/approve.html"

    def dispatch(self, request, *args, **kwargs):
        self.application = get_object_or_404(
            Application, pk=unhash_or_404(self.kwargs["pk_hash"])
        )

        if self.application.is_deleted:
            msg = f"Application {self.application.pk_hash} has been deleted, you need to restore it before you can approve it."
            messages.error(request, msg)
            return redirect("staff:application-list")

        if not hasattr(self.application, "studyinformationpage"):
            msg = "The Study Information page must be filled in before an Application can be approved."
            messages.error(request, msg)
            return redirect(self.application.get_staff_url())

        if self.application.approved_at:
            return redirect(self.application.get_staff_url())

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        org = form.cleaned_data["org"]
        project_name = form.cleaned_data["project_name"]
        project_number = form.cleaned_data["project_number"]

        # create Project with the chosen org
        project = org.projects.create(
            name=project_name,
            number=project_number,
            created_by=self.request.user,
            updated_by=self.request.user,
        )

        self.application.approved_at = timezone.now()
        self.application.approved_by = self.request.user
        self.application.project = project
        self.application.save()

        # redirect to the project since that's the object we've created
        return redirect(project.get_staff_url())

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "application": self.application,
        }

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {
            "orgs": fetch(Org.objects.order_by("name")),
        }

    def get_initial(self):
        project_number = Project.objects.filter(number__isnull=False).aggregate(
            largest_number=Max("number") + Value(1)
        )["largest_number"]

        # set the value of project_name from the study_name field in the
        # application form
        initial = {
            "project_name": self.application.studyinformationpage.study_name,
            "project_number": project_number,
        }

        # set the Org if a slug is included in the query args
        if org_slug := self.request.GET.get("org-slug"):
            try:
                initial["org"] = Org.objects.get(slug=org_slug)
            except Org.DoesNotExist:
                pass

        return initial


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ApplicationDetail(View):
    def dispatch(self, request, *args, **kwargs):
        self.application = get_object_or_404(
            Application.objects.select_related(
                "approved_by", "created_by", "deleted_by", "project"
            ),
            pk=unhash_or_404(self.kwargs["pk_hash"]),
        )

        if self.application.is_deleted:
            msg = f"Application {self.application.pk_hash} has been deleted, you need to restore it before you can view it."
            messages.error(request, msg)
            return redirect("staff:application-list")

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        wizard = Wizard(self.application, form_specs)
        pages = [page.review_context() for page in wizard.get_pages()]

        ctx = {
            "application": self.application,
            "researchers": fetch(
                self.application.researcher_registrations.order_by("created_at")
            ),
            "pages": pages,
        }

        return TemplateResponse(request, "staff/application/detail.html", ctx)

    def post(self, request, *args, **kwargs):
        wizard = Wizard(self.application, form_specs)
        pages = list(wizard.get_pages())

        review_time = timezone.now()

        for page in pages:
            form = page.get_bound_approval_form(request.POST)
            if form.instance.pk and form.has_changed():
                form.instance.last_reviewed_at = review_time
                form.instance.reviewed_by = request.user
                form.save()

        return redirect("staff:application-detail", self.application.pk_hash)


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ApplicationEdit(UpdateView):
    fields = [
        "status",
        "status_comment",
    ]
    model = Application
    response_class = TemplateResponse
    template_name = "staff/application/edit.html"

    def dispatch(self, request, *args, **kwargs):
        self.application = get_object_or_404(
            Application, pk=unhash_or_404(self.kwargs["pk_hash"])
        )

        if self.application.is_deleted:
            msg = f"Application {self.application.pk_hash} has been deleted, you need to restore it before you can edit it."
            messages.error(request, msg)
            return redirect("staff:application-list")

        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        # we're leaning heavily on UpdateView for this view, so instead of
        # overriding multiple methods to use self.application instead of the
        # expected self.object we can set it once here.
        return self.application

    def get_success_url(self):
        return self.object.get_staff_url()


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ApplicationList(ListView):
    response_class = TemplateResponse
    ordering = "-created_at"
    paginate_by = 25
    template_name = "staff/application/list.html"

    def get_context_data(self, **kwargs):
        # sort in Python because `User.name` is a property to pick either
        # get_full_name() or username depending on which one has been populated
        users = sorted(
            User.objects.filter(applications__isnull=False).distinct(),
            key=lambda u: u.name.lower(),
        )
        return super().get_context_data(**kwargs) | {
            "q": self.request.GET.get("q", ""),
            "statuses": Application.Statuses,
            "users": users,
        }

    def get_queryset(self):
        qs = Application.objects.select_related("created_by", "project").order_by(
            "-created_at"
        )

        if q := self.request.GET.get("q"):
            filters = {
                "created_by__fullname__icontains": q,
                "created_by__username__icontains": q,
                "researcher_registrations__name__icontains": q,
                "researcher_registrations__github_username__icontains": q,
            }

            # Application identifiers are hashes of their PK
            try:
                filters["pk"] = unhash(q)
            except ValueError:
                pass

            # build up Q objects OR'd together.  We need to build them with
            # functools.reduce so we can optionally add the PK filter to the
            # list
            qwargs = (Q(**{k: v}) for k, v in filters.items())
            qwargs = functools.reduce(Q.__or__, qwargs)

            qs = qs.filter(qwargs)

        if status := self.request.GET.get("status"):
            qs = qs.filter(status=status)

        if user := self.request.GET.get("user"):
            qs = qs.filter(created_by__username=user)

        return fetch(qs.distinct())


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ApplicationRemove(View):
    def post(self, request, *args, **kwargs):
        application = get_object_or_404(
            Application,
            pk=unhash_or_404(self.kwargs["pk_hash"]),
        )

        if application.is_approved:
            messages.error(request, "You cannot delete an approved Application.")
            return redirect(application.get_staff_url())

        if application.is_deleted:
            messages.error(request, "Application has already been deleted")
            return redirect(application.get_staff_url())

        application.deleted_at = timezone.now()
        application.deleted_by = request.user
        application.save()

        return redirect("staff:application-list")


@method_decorator(require_role(CoreDeveloper), name="dispatch")
class ApplicationRestore(View):
    def post(self, request, *args, **kwargs):
        application = get_object_or_404(
            Application,
            pk=unhash_or_404(self.kwargs["pk_hash"]),
        )

        if application.is_deleted:
            application.deleted_at = None
            application.deleted_by = None
            application.save()

        return redirect("staff:application-list")
