from django_filters import rest_framework as filters
from rest_framework import viewsets

from .models import Job, Workspace
from .serializers import JobShimSerializer, WorkspaceSerializer


class JobFilter(filters.FilterSet):
    backend = filters.CharFilter(field_name="job_request__backend")
    workspace = filters.NumberFilter(field_name="job_request__workspace_id")

    class Meta:
        fields = [
            "action_id",
            "backend",
            "needed_by_id",
            "started",
            "workspace",
        ]
        model = Job


class JobViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows jobs to be viewed or edited.
    """

    queryset = Job.objects.all().order_by("-created_at")
    serializer_class = JobShimSerializer
    filterset_class = JobFilter


class WorkspaceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows workspaces to be viewed or edited.
    """

    queryset = Workspace.objects.all().order_by("-created_at")
    serializer_class = WorkspaceSerializer
    filterset_fields = ("id", "name", "branch", "repo", "created_by__username", "db")
