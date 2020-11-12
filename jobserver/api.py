from django_filters import rest_framework as filters
from rest_framework import serializers, viewsets
from rest_framework.generics import ListAPIView

from .models import Job, JobRequest, Workspace
from .serializers import JobShimSerializer, WorkspaceSerializer


class WorkspaceSerializer2(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by.username", default=None)

    class Meta:
        fields = [
            "name",
            "repo",
            "branch",
            "db",
            "created_by",
            "created_at",
        ]
        model = Workspace


class JobRequestAPIList(ListAPIView):
    filterset_fields = ["backend"]
    permission_classes = []
    queryset = (
        JobRequest.objects.filter(
            jobs__completed_at__isnull=True,
        )
        .select_related("created_by", "workspace", "workspace__created_by")
        .order_by("-created_at")
        .distinct()
    )

    class serializer_class(serializers.ModelSerializer):
        created_by = serializers.CharField(source="created_by.username")
        workspace = WorkspaceSerializer2()

        class Meta:
            fields = [
                "backend",
                "sha",
                "identifier",
                "force_run_dependencies",
                "requested_actions",
                "created_by",
                "created_at",
                "workspace",
            ]
            model = JobRequest


class JobFilter(filters.FilterSet):
    action_id = filters.CharFilter(field_name="action")
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
