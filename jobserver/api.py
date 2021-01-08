import itertools
import operator

import structlog
from django.db import transaction
from first import first
from rest_framework import serializers
from rest_framework.exceptions import NotAuthenticated, ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Backend, JobRequest, Workspace


logger = structlog.get_logger(__name__)


def get_backend_from_token(token):
    """
    Token based authentication.

    DRF's authentication framework is tied to the concept of a User making
    requests and, sensibly, assumes you will populate request.user on
    successful authentication with the appropriate User instance.  However,
    we want to authenticate each Backend without mixing them up with our
    Human Users, so per-user auth doesn't make sense.  This function handles
    token-based auth and returns the relevant Backend on success.

    Clients should authenticate by passing their token in the
    "Authorization" HTTP header.  For example:

        Authorization: 401f7ac837da42b97f613d789819ff93537bee6a

    """

    if token is None:
        raise NotAuthenticated("Authorization header is missing")

    if token == "":
        raise NotAuthenticated("Authorization header is empty")

    try:
        return Backend.objects.get(auth_token=token)
    except Backend.DoesNotExist:
        raise NotAuthenticated("Invalid token")


class JobAPIUpdate(APIView):
    class serializer_class(serializers.Serializer):
        job_request_id = serializers.CharField()
        identifier = serializers.CharField()
        action = serializers.CharField(allow_blank=True)
        status = serializers.CharField()
        status_message = serializers.CharField(allow_blank=True)
        created_at = serializers.DateTimeField()
        updated_at = serializers.DateTimeField(allow_null=True)
        started_at = serializers.DateTimeField(allow_null=True)
        completed_at = serializers.DateTimeField(allow_null=True)

    def initial(self, request, *args, **kwargs):
        token = request.META.get("HTTP_AUTHORIZATION")

        # require auth for all requests
        self.backend = get_backend_from_token(token)

        return super().initial(request, *args, **kwargs)

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
            logger.info(
                f"About to delete jobs with identifiers: {','.join(jobs_by_identifier.keys())}",
                job_request=jr_identifier,
            )
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

    def initial(self, request, *args, **kwargs):
        token = request.META.get("HTTP_AUTHORIZATION")

        # if there's an Auth token then try to authenticate with that otherwise
        # ignore since this endpoint can be used either way.
        self.backend = get_backend_from_token(token) if token else None

        return super().initial(request, *args, **kwargs)

    def get_queryset(self):
        qs = (
            JobRequest.objects.filter(
                jobs__completed_at__isnull=True,
            )
            .select_related("created_by", "workspace", "workspace__created_by")
            .order_by("-created_at")
            .distinct()
        )

        # filter JobRequests by Backend name
        # Prioritise GET arg then self.backend (from authenticated requests)
        query_arg_backend = self.request.GET.get("backend", None)
        db_backend = getattr(self.backend, "name", None)
        if backend_name := first([query_arg_backend, db_backend]):
            qs = qs.filter(backend__name=backend_name)

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
