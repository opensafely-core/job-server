from django.db import transaction
from django_filters import rest_framework as filters
from rest_framework import serializers, viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Job, JobRequest, Workspace
from .serializers import JobShimSerializer, WorkspaceSerializer


class JobAPIUpdate(APIView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    class serializer_class(serializers.Serializer):
        # FIXME: these fields can be generated with a ModelSerializer once
        # we've migrated to v2 and removed v1-legacy Jobs.  Various fields
        # allow nulls/blank to handle the current late-v1 data, but we don't
        # want the v2 API to be so relaxed about our data types.
        job_request_id = serializers.CharField()
        identifier = serializers.CharField()
        action = serializers.CharField(allow_blank=True)
        status = serializers.CharField(source="runner_status")
        status_message = serializers.CharField(allow_blank=True)
        created_at = serializers.DateTimeField()
        updated_at = serializers.DateTimeField(allow_null=True)
        started_at = serializers.DateTimeField(allow_null=True)
        completed_at = serializers.DateTimeField(allow_null=True)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        job_request_ids = set(JobRequest.objects.values_list("identifier", flat=True))
        incoming_job_request_ids = {j["job_request_id"] for j in serializer.data}

        missing_ids = incoming_job_request_ids - job_request_ids
        if missing_ids:
            raise ValidationError(f"Unknown JobRequest IDs: {', '.join(missing_ids)}")

        job_requests = JobRequest.objects.filter(
            identifier__in=incoming_job_request_ids
        )
        job_request_lut = {jr.identifier: jr for jr in job_requests}

        # Remove existing jobs for the JobRequests we've been told about. POSTs
        # from job-runner are authoritive and declarative so the Jobs in a
        # given payload are the full set of Jobs the related JobRequests should
        # know about.
        Job.objects.filter(job_request__in=job_requests).delete()

        # create Jobs for each object in the payload
        jobs = []
        for job in serializer.data:
            jr_id = job.pop("job_request_id")
            status = job.pop("status")

            job_request = job_request_lut[jr_id]

            jobs.append(
                Job(
                    job_request=job_request,
                    runner_status=status,
                    **job,
                )
            )

        Job.objects.bulk_create(jobs)

        return Response({"status": "success"}, status=200)


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
