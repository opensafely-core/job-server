from rest_framework import viewsets

from .models import Job, Workspace
from .serializers import JobShimSerializer, WorkspaceSerializer


class JobViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows jobs to be viewed or edited.
    """

    queryset = Job.objects.all().order_by("-created_at")
    serializer_class = JobShimSerializer
    filterset_fields = (
        "job_request__workspace",
        "started",
        "job_request__backend",
        "action_id",
        "needed_by_id",
    )


class WorkspaceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows workspaces to be viewed or edited.
    """

    queryset = Workspace.objects.all().order_by("-created_at")
    serializer_class = WorkspaceSerializer
    filterset_fields = ("id", "name", "branch", "repo", "created_by__username", "db")
