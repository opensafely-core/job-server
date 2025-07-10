import datetime
import json
from collections import defaultdict

import structlog
from django.db.models import Q
from django.http import Http404
from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from jobserver.api.authentication import get_backend_from_token
from jobserver.emails import send_finished_notification
from jobserver.models import Job, JobRequest, Stats, User, Workspace


COMPLETED_STATES = {"failed", "succeeded"}


logger = structlog.get_logger(__name__)


class CoercingCharFieldSerializer(serializers.CharField):
    def run_validation(self, data=serializers.empty):
        (is_empty_value, data) = self.validate_empty_values(data)

        # coerce the empty value to an empty string here.  Using default=""
        # makes the field optional which we don't want, and to_internal_value
        # is only called if the field isn't classed as empty, so in the case of
        # getting null/None any coercion in that field doesn't fire, so we're
        # stuck with overriding this method.
        if is_empty_value:
            return ""

        value = self.to_internal_value(data)
        self.run_validators(value)
        return value


def update_backend_state(backend, request):
    # Retrieve backend state sent up from job-runner. We might rename the header this is
    # passed in at some point but for now this is good enough.
    flags = request.headers.get("Flags", "")
    if not flags:
        return

    jobrunner_state = json.loads(flags)

    # Record the time we're told this backend was last seen alive, for availability
    # reporting purposes
    if last_seen_at_flag := jobrunner_state.get("last-seen-at"):
        last_seen_at_dt = datetime.datetime.fromisoformat(last_seen_at_flag["v"])
        Stats.objects.update_or_create(
            backend=backend,
            url=request.path,
            defaults={"api_last_seen": last_seen_at_dt},
        )

    backend.jobrunner_state = jobrunner_state
    backend.save(update_fields=["jobrunner_state"])


class JobAPIUpdate(APIView):
    authentication_classes = [SessionAuthentication]

    class serializer_class(serializers.Serializer):
        # Note job_request_id maps to JobRequest.identifier, not JobRequest.id
        job_request_id = serializers.CharField()
        identifier = serializers.CharField()
        action = serializers.CharField(allow_blank=True)
        run_command = CoercingCharFieldSerializer(allow_blank=True, allow_null=True)
        status = serializers.CharField()
        status_code = serializers.CharField(allow_blank=True)
        status_message = serializers.CharField(allow_blank=True)
        created_at = serializers.DateTimeField()
        updated_at = serializers.DateTimeField(allow_null=True)
        started_at = serializers.DateTimeField(allow_null=True)
        completed_at = serializers.DateTimeField(allow_null=True)
        trace_context = serializers.JSONField(allow_null=True, required=False)
        metrics = serializers.JSONField(allow_null=True, required=False)

    def initial(self, request, *args, **kwargs):
        token = request.headers.get("Authorization")

        # require auth for all requests
        self.backend = get_backend_from_token(token)

        return super().initial(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        # get JobRequest instances based on the identifiers in the payload
        incoming_job_request_ids = {
            j["job_request_id"] for j in serializer.validated_data
        }
        job_requests = JobRequest.objects.filter(
            identifier__in=incoming_job_request_ids
        )
        job_request_lut = {jr.identifier: jr for jr in job_requests}

        # Map JobRequest identifiers to lists of associated Job instances for iteration.
        jobs_by_request = defaultdict(list)
        for job in serializer.validated_data:
            jobs_by_request[job["job_request_id"]].append(job)

        created_job_ids = []
        updated_job_ids = []

        for jr_identifier, jobs in jobs_by_request.items():
            jobs = list(jobs)

            # get the JobRequest for this identifier
            job_request = job_request_lut.get(jr_identifier)
            if job_request is None:
                # we don't expect this to happen under normal circumstances, but it's
                # now no longer a protocol violation for job-runner to tell us about
                # JobRequests we didn't ask about, so we shouldn't error here
                logger.info(
                    "Ignoring unrecognised JobRequest", job_request_id=jr_identifier
                )
                continue

            # bind the job request ID to further logs so looking them up in the UI is easier
            structlog.contextvars.bind_contextvars(job_request=job_request.id)

            database_jobs = job_request.jobs.all()

            # get the current Jobs for the JobRequest, keyed on their identifier
            jobs_by_identifier = {j.identifier: j for j in database_jobs}

            payload_identifiers = {j["identifier"] for j in jobs}

            # delete local jobs not in the payload
            identifiers_to_delete = set(jobs_by_identifier.keys()) - payload_identifiers
            if identifiers_to_delete:
                job_request.jobs.filter(identifier__in=identifiers_to_delete).delete()

            for job_data in jobs:
                # remove this value from the data, it's going to be set by
                # creating/updating Job instances via the JobRequest instances
                # related Jobs manager (ie job_request.jobs)
                job_data.pop("job_request_id")

                job, created = job_request.jobs.get_or_create(
                    identifier=job_data["identifier"],
                    defaults={**job_data},
                )

                if created:
                    created_job_ids.append(str(job.id))
                    # For newly created jobs we can't tell if they've just transitioned
                    # to completed so we assume they have to avoid missing notifications
                    newly_completed = job_data["status"] in COMPLETED_STATES
                else:
                    updated_job_ids.append(str(job.id))
                    # check to see if the Job is about to transition to completed
                    # (failed or succeeded) so we can notify after the update
                    newly_completed = (
                        job.status not in COMPLETED_STATES
                        and job_data["status"] in COMPLETED_STATES
                    )

                    # update Job "manually" so we can make the check above for
                    # status transition
                    for key, value in job_data.items():
                        setattr(job, key, value)
                    job.save()

                # We only send notifications or alerts for newly completed jobs
                if newly_completed:
                    # round trip the Job to the db so all fields are converted to their
                    # python representations as expected by the notification code
                    job.refresh_from_db()
                    handle_job_notifications(job_request, job)

        logger.info(
            "Created or updated Jobs",
            created_job_ids=",".join(created_job_ids),
            updated_job_ids=",".join(updated_job_ids),
        )

        update_backend_state(self.backend, request)

        return Response({"status": "success"}, status=200)


def handle_job_notifications(job_request, job):
    if job_request.will_notify:
        send_finished_notification(
            job_request.created_by.email,
            job,
        )
        logger.info(
            "Notified requesting user of completed job",
            user_id=job_request.created_by_id,
        )


class WorkspaceSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by.username", default=None)
    repo = serializers.CharField(source="repo.url", default=None)

    class Meta:
        fields = [
            "name",
            "repo",
            "branch",
            "created_by",
            "created_at",
        ]
        model = Workspace


class JobRequestAPIList(ListAPIView):
    authentication_classes = []

    class serializer_class(serializers.ModelSerializer):
        backend = serializers.CharField(source="backend.slug")
        created_by = serializers.CharField(source="created_by.username")
        workspace = WorkspaceSerializer()
        project = serializers.CharField(source="workspace.project.slug")
        orgs = serializers.SerializerMethodField()

        class Meta:
            fields = [
                "backend",
                "sha",
                "identifier",
                "force_run_dependencies",
                "requested_actions",
                "cancelled_actions",
                "created_by",
                "created_at",
                "workspace",
                "database_name",
                "project",
                "orgs",
                "codelists_ok",
            ]
            model = JobRequest

        def get_orgs(self, obj):
            return list(obj.workspace.project.orgs.values_list("slug", flat=True))

    def initial(self, request, *args, **kwargs):
        token = request.headers.get("Authorization")

        # if there's an Auth token then try to authenticate with that otherwise
        # ignore since this endpoint can be used either way.
        self.backend = get_backend_from_token(token) if token else None

        return super().initial(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        # only update state when authenticated and response is 2xx
        if self.backend and response.status_code >= 200 and response.status_code < 300:
            update_backend_state(self.backend, request)

        return response

    def get_queryset(self):
        active_job_request_ids = (
            Job.objects.filter(status__in=["pending", "running"])
            .values_list("job_request_id")
            .distinct()
        )
        # A job request is acknowledged by the RAP Controller when it has at least one
        # job created for it
        acknowledged_job_request_ids = (
            Job.objects.all().values_list("job_request_id").distinct()
        )
        qs = (
            JobRequest.objects.filter(
                Q(id__in=active_job_request_ids)
                | ~Q(id__in=acknowledged_job_request_ids),
            )
            .select_related(
                "backend",
                "created_by",
                "workspace",
                "workspace__created_by",
                "workspace__project",
                "workspace__repo",
            )
            .prefetch_related("workspace__project__orgs")
            .order_by("-created_at")
        )

        backend_slug = getattr(self.backend, "slug", None)
        if backend_slug is not None:
            qs = qs.filter(backend__slug=backend_slug)

        return qs


class UserAPIDetail(APIView):
    authentication_classes = []

    def initial(self, request, *args, **kwargs):
        token = request.headers.get("Authorization")

        # require auth for all requests
        self.backend = get_backend_from_token(token)

        return super().initial(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(username=self.kwargs["username"])
        except User.DoesNotExist:
            raise Http404

        data = {
            "permissions": user.get_all_permissions(),
            "roles": user.get_all_roles(),
        }
        return Response(data, status=200)


class WorkspaceStatusesAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = []

    def get(self, request, *args, **kwargs):
        try:
            workspace = Workspace.objects.get(name=self.kwargs["name"])
        except Workspace.DoesNotExist:
            return Response(status=404)

        backend = request.GET.get("backend", None)
        actions_with_status = workspace.get_action_status_lut(backend)
        return Response(actions_with_status, status=200)
