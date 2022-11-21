import itertools
import json
import operator

import sentry_sdk
import structlog
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils import timezone
from pipeline import load_pipeline
from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import NotAuthenticated
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from jobserver.api.authentication import get_backend_from_token
from jobserver.emails import send_finished_notification
from jobserver.models import Backend, JobRequest, Stats, User, Workspace


logger = structlog.get_logger(__name__)


def update_stats(backend, url):
    Stats.objects.update_or_create(
        backend=backend,
        url=url,
        defaults={"api_last_seen": timezone.now()},
    )


class JobAPIUpdate(APIView):
    authentication_classes = [SessionAuthentication]

    class serializer_class(serializers.Serializer):
        job_request_id = serializers.CharField()
        identifier = serializers.CharField()
        action = serializers.CharField(allow_blank=True)
        status = serializers.CharField()
        status_code = serializers.CharField(allow_blank=True)
        status_message = serializers.CharField(allow_blank=True)
        created_at = serializers.DateTimeField()
        updated_at = serializers.DateTimeField(allow_null=True)
        started_at = serializers.DateTimeField(allow_null=True)
        completed_at = serializers.DateTimeField(allow_null=True)
        trace_context = serializers.JSONField(allow_null=True, required=False)

    def initial(self, request, *args, **kwargs):
        token = request.headers.get("Authorization")

        # require auth for all requests
        self.backend = get_backend_from_token(token)

        return super().initial(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        # get JobRequest instances based on the identifiers in the payload
        incoming_job_request_ids = {j["job_request_id"] for j in serializer.data}
        job_requests = JobRequest.objects.filter(
            identifier__in=incoming_job_request_ids
        )
        job_request_lut = {jr.identifier: jr for jr in job_requests}

        # sort the incoming data by JobRequest identifier to ensure the
        # subsequent groupby call works correctly.
        job_requests = sorted(
            serializer.data, key=operator.itemgetter("job_request_id")
        )
        # group Jobs by their JobRequest ID
        jobs_by_request = itertools.groupby(
            serializer.data, key=operator.itemgetter("job_request_id")
        )
        created_job_ids = []
        updated_job_ids = []
        for jr_identifier, jobs in jobs_by_request:
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

                if not created:
                    updated_job_ids.append(str(job.id))
                    # check to see if the Job is about to transition to completed
                    # (failed or succeeded) so we can notify after the update
                    completed = ["failed", "succeeded"]
                    newly_completed = (
                        job.status not in completed and job_data["status"] in completed
                    )

                    # update Job "manually" so we can make the check above for
                    # status transition
                    for key, value in job_data.items():
                        setattr(job, key, value)
                    job.save()
                    job.refresh_from_db()

                else:
                    created_job_ids.append(str(job.id))
                    # For newly created jobs we can't check if they've just
                    # transition to "completed" so we knowingly skip potential
                    # notifications here to avoid creating false positives.
                    newly_completed = False

                # We only send notifications or alerts for newly completed jobs
                if newly_completed:
                    handle_alerts_and_notifications(request, job_request, job)

        logger.info(
            "Created or updated Jobs",
            created_job_ids=",".join(created_job_ids),
            updated_job_ids=",".join(updated_job_ids),
        )

        # store backend state sent up from job-runner.  We might rename the
        # header this is passed in at some point but now this is good enough.
        if flags := request.headers.get("Flags", ""):
            self.backend.jobrunner_state = json.loads(flags)
            self.backend.save(update_fields=["jobrunner_state"])

        # record use of the API
        update_stats(self.backend, request.path)

        return Response({"status": "success"}, status=200)


def handle_alerts_and_notifications(request, job_request, job):
    error_messages = {
        "internal error": "Job encountered an internal error",
        "something went wrong with the database": "Job encountered an unexpected database error",
        "ran out of memory": "Job encountered an out of memory error",
    }

    for message_fragment, sentry_message in error_messages.items():
        if message_fragment in job.status_message.lower():
            # bubble errors encountered with a job up to
            # sentry so we can get notifications they've happened
            with sentry_sdk.push_scope() as scope:
                scope.set_tag("backend", job_request.backend.slug)
                scope.set_tag("job", request.build_absolute_uri(job.get_absolute_url()))
                scope.set_tag(
                    "docs",
                    "https://github.com/opensafely-core/backend-server/blob/main/jobrunner/playbook.md",
                )
                sentry_sdk.capture_message(sentry_message)
            break

    if job_request.will_notify:
        send_finished_notification(
            job_request.created_by.notifications_email,
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
            "db",
            "created_by",
            "created_at",
        ]
        model = Workspace


class JobRequestAPIListCreate(APIView):
    """
    Dispatcher view for the /job-requests/ endpoint.

    The handlers for the GET and POST verbs are very different in this
    endpoint.  Those differences are encapsulated in the Views we hand off to
    in this one.
    """

    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() == "post":
            return JobRequestAPICreate().dispatch(request, *args, **kwargs)

        return JobRequestAPIList().dispatch(request, *args, **kwargs)


class JobRequestAPICreate(APIView):
    authentication_classes = []

    class serializer_class(serializers.ModelSerializer):
        backend = serializers.SlugRelatedField(
            slug_field="slug", queryset=Backend.objects.all()
        )
        workspace = serializers.SlugRelatedField(
            slug_field="name", queryset=Workspace.objects.all()
        )

        class Meta:
            fields = [
                "backend",
                "workspace",
                "sha",
                "project_definition",
                "requested_actions",
                "force_run_dependencies",
            ]
            model = JobRequest

        def validate_project_definition(self, value):
            load_pipeline(value)

            return value

    def post(self, request, *args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if auth_header is None:
            raise NotAuthenticated("Authorization header missing")

        username, _, token = auth_header.partition(":")
        user = User.objects.filter(username=username).first()

        if user is None:
            raise NotAuthenticated("Invalid user")

        if not user.has_valid_pat(token):
            raise PermissionDenied()

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        job_request = serializer.save(created_by=user)

        # link to the JobRequest's detail page
        url = request.build_absolute_uri(job_request.get_absolute_url())

        return Response({"url": url}, status=201)


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
                "project",
                "orgs",
            ]
            model = JobRequest

        def get_orgs(self, obj):
            return [obj.workspace.project.org.slug]

    def initial(self, request, *args, **kwargs):
        token = request.headers.get("Authorization")

        # if there's an Auth token then try to authenticate with that otherwise
        # ignore since this endpoint can be used either way.
        self.backend = get_backend_from_token(token) if token else None

        return super().initial(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        # only gather stats when authenticated and response is 2xx
        if self.backend and response.status_code >= 200 and response.status_code < 300:
            update_stats(self.backend, request.path)

        return response

    def get_queryset(self):
        qs = (
            JobRequest.objects.filter(
                jobs__completed_at__isnull=True,
            )
            .select_related(
                "created_by",
                "workspace",
                "workspace__created_by",
                "workspace__project",
                "workspace__project__org",
            )
            .order_by("-created_at")
            .distinct()
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
