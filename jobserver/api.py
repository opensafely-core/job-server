import itertools
import operator

from django.db import transaction
from rest_framework import serializers
from rest_framework.authentication import BasicAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import JobRequest, Workspace


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
        status = serializers.CharField()
        status_message = serializers.CharField(allow_blank=True)
        created_at = serializers.DateTimeField()
        updated_at = serializers.DateTimeField(allow_null=True)
        started_at = serializers.DateTimeField(allow_null=True)
        completed_at = serializers.DateTimeField(allow_null=True)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        incoming_job_request_ids = {j["job_request_id"] for j in serializer.data}

        # error if we find JobRequest IDs in the payload which aren't in the database.
        job_request_ids = set(JobRequest.objects.values_list("identifier", flat=True))
        missing_ids = incoming_job_request_ids - job_request_ids
        if missing_ids:
            raise ValidationError(f"Unknown JobRequest IDs: {', '.join(missing_ids)}")

        # get JobRequest instances based on the identifiers in the payload
        job_requests = JobRequest.objects.filter(
            identifier__in=incoming_job_request_ids
        )
        job_request_lut = {jr.identifier: jr for jr in job_requests}

        # group Jobs by their JobRequest ID
        jobs_by_request = itertools.groupby(
            serializer.data, key=operator.itemgetter("job_request_id")
        )
        for jr_identifier, jobs in jobs_by_request:
            # get the JobRequest for this identifier
            job_request = job_request_lut[jr_identifier]

            # get the current Jobs for the JobRequest, keyed on their identifier
            jobs_by_identifier = {j.identifier: j for j in job_request.jobs.all()}

            # delete local jobs not in the payload
            job_request.jobs.exclude(identifier__in=jobs_by_identifier.keys()).delete()

            for job_data in jobs:
                # remove this value from the data, it's going to be set by
                # creating/updating Job instances via the JobRequest instances
                # related Jobs manager (ie job_request.jobs)
                job_data.pop("job_request_id")

                job_request.jobs.update_or_create(
                    identifier=job_data["identifier"],
                    defaults={**job_data},
                )

        return Response({"status": "success"}, status=200)


class WorkspaceSerializer(serializers.ModelSerializer):
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
    class serializer_class(serializers.ModelSerializer):
        backend = serializers.CharField(source="backend.name")
        created_by = serializers.CharField(source="created_by.username")
        workspace = WorkspaceSerializer()

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

    def get_queryset(self):
        qs = (
            JobRequest.objects.filter(
                jobs__completed_at__isnull=True,
            )
            .select_related("created_by", "workspace", "workspace__created_by")
            .order_by("-created_at")
            .distinct()
        )

        backend = self.request.GET.get("backend")
        if backend:
            qs = qs.filter(backend__name=backend)

        return qs


class WorkspaceStatusesAPI(APIView):
    permission_classes = []

    def get(self, request, *args, **kwargs):
        try:
            workspace = Workspace.objects.get(name=self.kwargs["name"])
        except Workspace.DoesNotExist:
            return Response(status=404)

        actions_with_status = workspace.get_action_status_lut()
        return Response(actions_with_status, status=200)
