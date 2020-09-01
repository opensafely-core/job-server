from jobserver.api.models import Job
from jobserver.api.models import Workspace
from jobserver.api.serializers import JobSerializer
from jobserver.api.serializers import WorkspaceSerializer

from rest_framework import viewsets


class JobViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows jobs to be viewed or edited.
    """

    queryset = Job.objects.all().order_by("-created_at")
    serializer_class = JobSerializer
    filterset_fields = ("workspace", "started", "backend", "action")


class WorkspaceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows workspaces to be viewed or edited.
    """

    queryset = Workspace.objects.all().order_by("-created_at")
    serializer_class = WorkspaceSerializer
    filterset_fields = ("id", "name", "branch", "repo", "owner", "db")
