from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.views.generic import View

from ..models import Project


class Releases(View):
    def get(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project,
            slug=self.kwargs["project_slug"],
            org__slug=self.kwargs["org_slug"],
        )

        # TODO: check ACL and build signed URLs here

        context = {
            "project": project,
        }
        return TemplateResponse(
            request,
            "project_releases.html",
            context=context,
        )
