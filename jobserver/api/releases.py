from email.message import Message
from pathlib import Path

import sentry_sdk
import structlog
from django.conf import settings
from django.db import transaction
from django.db.models import Value
from django.shortcuts import get_object_or_404
from django.utils import timezone
from opentelemetry import trace
from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import (
    NotAuthenticated,
    ParseError,
    PermissionDenied,
    ValidationError,
)
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.parsers import FileUploadParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from interactive.commands import create_report
from interactive.emails import send_report_uploaded_notification
from interactive.models import AnalysisRequest
from interactive.slacks import notify_report_uploaded
from jobserver import releases, slacks
from jobserver.api.authentication import get_backend_from_token
from jobserver.authorization import OutputChecker, has_permission, has_role, permissions
from jobserver.commands import users
from jobserver.models import (
    Project,
    PublishRequest,
    Release,
    ReleaseFile,
    ReleaseFileReview,
    Snapshot,
    User,
    Workspace,
)
from jobserver.releases import serve_file
from jobserver.utils import set_from_qs

from ..github import _get_github_api


logger = structlog.get_logger(__name__)


def get_filename(headers):
    """
    Get the filename from the Content-Disposition header

    DRF validates and parses the Content-Disposition header, but sadly
    strips any directory paths from the filename. We need those paths, so
    we need to reparse the header to get them.
    """
    m = Message()
    m["Content-Disposition"] = headers["Content-Disposition"]
    return m.get_filename()


def is_interactive_report(rfile):
    """
    Is the given ReleaseFile for an Interactive Report?

    We match released outputs to their AnalysisRequest by setting the output
    filenames in their project.yaml to

        output/{{ analysis_request.pk }}/report.html

    This function looks for HTML files with a name matching an AnalysisRequest
    PK, banking on ULIDs being unique enough for there to not be a clash here.

    It returns AnalysisRequest | None so it can be used with a walrus-like
    check.
    """

    path = Path(rfile.name)
    if (
        len(path.parts) == 3
        and path.parts[0] == "output"
        and path.parts[2] == "report.html"
    ):
        identifier = path.parts[1]
    else:
        return

    return AnalysisRequest.objects.filter(pk=identifier).first()


def to_mb(value_in_bytes):
    """Convert given value to Mb"""
    size = round(value_in_bytes / (1024 * 1024), 2)

    return f"{size}Mb"


class UnknownFiles(Exception):
    pass


class ReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ReleaseFileReview.Statuses.choices)
    comments = serializers.DictField()


class FileSerializer(serializers.Serializer):
    name = serializers.CharField()
    url = serializers.CharField()
    size = serializers.IntegerField()
    sha256 = serializers.CharField()
    date = serializers.DateTimeField()
    metadata = serializers.DictField()
    review = ReviewSerializer(allow_null=True)

    def validate(self, data):
        size = data["size"]
        if size <= settings.RELEASE_FILE_SIZE_LIMIT:
            return data

        size = to_mb(size)  # convert size for easier display
        raise serializers.ValidationError(
            {"size": f"File size should be <16Mb. {data['name']} is {size}Mb"}
        )


class ReleaseSerializer(serializers.Serializer):
    files = FileSerializer(many=True)
    metadata = serializers.DictField()
    review = serializers.DictField(allow_null=True)


class ReleaseNotificationAPICreate(CreateAPIView):
    authentication_classes = [SessionAuthentication]

    class serializer_class(serializers.Serializer):
        created_by = serializers.CharField()
        path = serializers.CharField()
        files = serializers.ListField(
            child=serializers.CharField(), required=False, default=None
        )

    def initial(self, request, *args, **kwargs):
        token = request.headers.get("Authorization")

        # require auth for all requests
        self.backend = get_backend_from_token(token)

        return super().initial(request, *args, **kwargs)

    def perform_create(self, serializer):
        kwargs = serializer.data
        kwargs["backend"] = self.backend
        slacks.notify_github_release(**kwargs)


def validate_files(db_files, payload_files):
    # check all the listed files already exist
    existing_files = {f.name: f.filehash for f in db_files}
    reviewed_files = {f["name"]: f["sha256"] for f in payload_files}

    unknown_filenames = reviewed_files.keys() - existing_files.keys()
    known_files = {
        k: v for k, v in reviewed_files.items() if k not in unknown_filenames
    }
    mismatched_hashes = known_files.items() - existing_files.items()

    if not (unknown_filenames and mismatched_hashes):
        return

    msg = []

    for unknown in unknown_filenames:
        msg.append(f"Unknown file {unknown}")
    for name, sha in mismatched_hashes:
        msg.append(f"Expected sha {sha} for file {name}")

    raise UnknownFiles(msg)


def validate_upload_access(request, workspace):
    """Validate the request can upload releases for this workspace.

    This validation uses backend authentication to authenticate the user, but
    then checks that user has the correct permissons."""
    # authenticate and get backend
    backend = get_backend_from_token(request.headers.get("Authorization"))

    # The request is from an authenticated backend so we trust it to supply
    # arbitrary usernames
    username = request.headers.get("OS-User", "").strip()
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise NotAuthenticated

    # check the user has access to this backend
    if user not in backend.members.all():
        raise NotAuthenticated

    # check the user has permission to upload release files
    if not has_permission(
        user, permissions.release_file_upload, project=workspace.project
    ):
        raise NotAuthenticated

    return backend, user


def validate_release_access(request, workspace):
    """Validate this request can access releases for this workspace.

    This validation uses a User PAT OR Django's regular User auth.
    """
    if auth_header := request.headers.get("Authorization"):
        username, _, token = auth_header.partition(":")

        user = User.objects.filter(username=username).first()
        if user is None:
            raise NotAuthenticated("Invalid user")

        if not user.has_valid_pat(token):
            raise PermissionDenied

        return

    if request.user.is_anonymous:
        raise NotAuthenticated("Invalid user or token")

    if not has_permission(
        request.user, permissions.release_file_view, project=workspace.project
    ):
        raise NotAuthenticated(f"Invalid user or token for workspace {workspace.name}")


def validate_snapshot_access(request, snapshot):
    """
    Validate this request can access this snapshot.

    This validation uses Django's regular User auth.
    """
    if snapshot.is_published:
        return

    if request.user.is_anonymous:
        raise NotAuthenticated("Invalid user or token")

    if not has_permission(
        request.user, permissions.release_file_view, project=snapshot.workspace.project
    ):
        raise NotAuthenticated(f"Invalid user or token for snapshot pk={snapshot.pk}")


def generate_index(files):
    """Generate a JSON list of files as expected by the SPA."""

    output = dict(
        files=[
            dict(
                name=name,
                id=rfile.pk,
                url=rfile.get_api_url(),
                user=rfile.created_by.username,
                date=rfile.created_at.isoformat(),
                sha256=rfile.filehash,
                size=rfile.size,
                is_deleted=rfile.is_deleted,
                backend=rfile.release.backend.name,
                metadata=rfile.metadata,
                review=None,
            )
            for name, rfile in files.items()
        ],
    )

    # validate our output data with the serializer, without having to encode
    # all the source lookups into the serializer itself
    FileSerializer(data=output, many=True).is_valid()

    return output


class ReleaseWorkspaceAPI(APIView):
    """Listing current files and creating new Releases for a workspace."""

    authentication_classes = [SessionAuthentication]
    get_github_api = staticmethod(_get_github_api)
    parsers = [JSONParser]

    def post(self, request, workspace_name):
        """Create a new Release for this workspace."""
        workspace = get_object_or_404(Workspace, name=workspace_name)
        backend, user = validate_upload_access(request, workspace)

        # parse the requested files
        serializer = ReleaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        files = serializer.validated_data["files"]
        metadata = serializer.validated_data["metadata"]
        release_id = metadata.pop("airlock_id", None)

        try:
            release = releases.create_release(
                workspace, backend, user, files, metadata=metadata, id=release_id
            )
        except releases.ReleaseFileAlreadyExists as exc:
            raise ValidationError({"detail": str(exc)})

        slacks.notify_release_created(release)

        # Current osrelease workflow should not create a Github issues, so allow that to be supressed
        # Note: this is broken and spamming issues, so comment out for now
        # if request.headers.get("Suppress-Github-Issue") is None:  # pragma: no cover
        #   issues.create_output_checking_request(release, self.get_github_api())

        body = {
            "release_id": str(release.id),
            "release_url": request.build_absolute_uri(release.get_absolute_url()),
        }

        response = Response(body, status=201)
        # this is required for osrelease currently
        response["Release-Id"] = str(release.id)
        return response

    def get(self, request, workspace_name):
        """List the most recent versions of files for the Workspace."""
        workspace = get_object_or_404(Workspace, name=workspace_name)
        validate_release_access(request, workspace)
        files = releases.workspace_files(workspace)
        return Response(generate_index(files))


class ReleaseAPI(APIView):
    authentication_classes = [SessionAuthentication]

    # DRF file upload does not use multipart, is just a simple byte stream
    parser_classes = [FileUploadParser]

    def post(self, request, release_id):
        """Upload a file for this Release.

        File must be listed in Release.requested_files, and the hash must match.
        """
        release = get_object_or_404(Release, id=release_id)
        backend, user = validate_upload_access(request, release.workspace)

        # Django's InMemoryUploadedFile only reads the number of bytes
        # specified in the Content-Length header so we can rely on just
        # checking that instead of checking the file size as well.
        content_length = request.headers.get("Content-Length")
        if content_length and int(content_length) > settings.RELEASE_FILE_SIZE_LIMIT:
            size_limit = to_mb(settings.RELEASE_FILE_SIZE_LIMIT)
            raise ValidationError(f"File is too large, it must be below {size_limit}")

        try:
            upload = request.data["file"]
        except KeyError:
            raise ValidationError({"detail": "No data uploaded"})

        filename = get_filename(request.headers)

        if filename not in {f["name"] for f in release.requested_files}:
            raise ValidationError(
                {"detail": f"File {filename} not requested in release {release.id}"}
            )

        # ensure this is being released from the same backend as the Release
        # was created from
        if release.backend != backend:
            raise ValidationError(
                {
                    "detail": f"Release is from backend {release.backend.slug} not {backend.slug}"
                }
            )

        try:
            rfile = releases.handle_file_upload(
                release, backend, user, upload, filename
            )
        except (
            releases.ReleaseFileAlreadyExists,
            releases.ReleaseFileHashMismatch,
        ) as exc:
            raise ValidationError({"detail": str(exc)})

        slacks.notify_release_file_uploaded(rfile)

        if analysis_request := is_interactive_report(rfile):
            with transaction.atomic():
                create_report(
                    analysis_request=analysis_request,
                    rfile=rfile,
                    user=analysis_request.created_by,
                )

                send_report_uploaded_notification(analysis_request)
                notify_report_uploaded(analysis_request)

        response = Response(status=201)
        response.headers["File-Id"] = rfile.id
        response.headers["Location"] = request.build_absolute_uri(rfile.get_api_url())
        return response

    def get(self, request, release_id):
        """A list of files for this Release."""
        release = get_object_or_404(Release, id=release_id)
        validate_release_access(request, release.workspace)
        files = {f.name: f for f in release.files.select_related("created_by")}
        return Response(generate_index(files))


class ReleaseFileAPI(APIView):
    authentication_classes = [SessionAuthentication]

    def get(self, request, file_id):
        """Return the content of a specific ReleaseFile"""
        # treat a deleted file as missing
        release_files = ReleaseFile.objects.filter(deleted_at=None, deleted_by=None)
        rfile = get_object_or_404(release_files, id=file_id)
        validate_release_access(request, rfile.workspace)
        return serve_file(request, rfile)


class ReviewAPI(APIView):
    authentication_classes = [SessionAuthentication]

    def post(self, request, *args, **kwargs):
        release = get_object_or_404(Release, id=self.kwargs["release_id"])
        db_files = release.files.all()

        serializer = ReleaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload_files = serializer.validated_data["files"]

        try:
            validate_files(db_files, payload_files)
        except UnknownFiles as e:
            sentry_sdk.capture_exception(e)
            raise ValidationError(e)

        with transaction.atomic():
            release.review = serializer.validated_data["review"]
            release.save(update_fields=["review"])

            created_at = timezone.now()  # reviews are created at the same time

            # create review objects for each file in the files list
            for file in payload_files:
                rfile = db_files.get(name=file["name"], filehash=file["sha256"])

                rfile.reviews.create(
                    created_at=created_at,
                    created_by=request.user,
                    status=file["review"]["status"],
                    comments=file["review"]["comments"],
                )

        return Response()


class SnapshotAPI(APIView):
    authentication_classes = [SessionAuthentication]

    def get(self, request, *args, **kwargs):
        """A list of files for this Snapshot."""
        snapshot = get_object_or_404(
            Snapshot,
            workspace__name=self.kwargs["workspace_id"],
            pk=self.kwargs["snapshot_id"],
        )

        validate_snapshot_access(request, snapshot)
        files = {
            f.name: f
            for f in snapshot.files.select_related(
                "created_by",
                "release",
                "release__backend",
                "workspace",
                "workspace__project",
            ).annotate(is_published=Value(snapshot.is_published))
        }

        return Response(generate_index(files))


class SnapshotCreateAPI(APIView):
    authentication_classes = [SessionAuthentication]

    class serializer_class(serializers.Serializer):
        file_ids = serializers.ListField(child=serializers.CharField())

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """Create a Snapshot from the given list of files."""
        workspace = get_object_or_404(Workspace, name=self.kwargs["workspace_id"])

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data

        if not has_permission(
            request.user, permissions.snapshot_create, project=workspace.project
        ):
            raise NotAuthenticated

        file_ids = set(data["file_ids"])
        files = ReleaseFile.objects.filter(pk__in=file_ids)

        # check all ReleaseFile IDs submitted are valid IDs
        if missing := file_ids - set_from_qs(files):
            raise ParseError(f"Unknown file IDs: {', '.join(missing)}")

        publish_request = PublishRequest.create_from_files(
            files=files, user=request.user
        )

        return Response(
            {"url": publish_request.snapshot.get_absolute_url()}, status=201
        )


class SnapshotPublishAPI(APIView):
    authentication_classes = [SessionAuthentication]

    def post(self, request, *args, **kwargs):
        snapshot = get_object_or_404(
            Snapshot,
            workspace__name=self.kwargs["workspace_id"],
            pk=self.kwargs["snapshot_id"],
        )

        if not has_permission(
            request.user,
            permissions.snapshot_publish,
            project=snapshot.workspace.project,
        ):
            raise NotAuthenticated

        publish_request = snapshot.publish_requests.order_by("-created_at").first()

        if publish_request is None:
            # a snapshot should never exist without a publish request, how did
            # we get here?
            raise Exception("Snapshot is missing publish request")

        if publish_request.decision == PublishRequest.Decisions.APPROVED:
            # The Snapshot has already been published, don't lose the original
            # information.
            return Response()

        publish_request.approve(user=request.user)

        return Response()


class WorkspaceStatusAPI(RetrieveAPIView):
    authentication_classes = [SessionAuthentication]
    lookup_field = "name"
    lookup_url_kwarg = "workspace_id"
    queryset = Workspace.objects.all()

    class serializer_class(serializers.Serializer):
        uses_new_release_flow = serializers.BooleanField()


class Level4AuthenticatedUser(serializers.Serializer):
    username = serializers.CharField()
    fullname = serializers.CharField()
    workspaces = serializers.DictField(default={})
    output_checker = serializers.BooleanField()
    staff = serializers.BooleanField()


def build_level4_user(user):
    ongoing_project_statuses = {
        Project.Statuses.ONGOING,
        Project.Statuses.ONGOING_LINKED,
    }

    workspaces = {}
    # this is 1 or 2 queries per project, not ideal, but we permissions are not stored in the db
    for project in user.projects.all():
        if has_permission(user, permissions.unreleased_outputs_view, project=project):
            for workspace in project.workspaces.all().values("name", "is_archived"):
                workspaces[workspace["name"]] = {
                    "project": project.name,  # for backwards compatibility with Airlock
                    "project_details": {
                        "name": project.name,
                        "ongoing": project.status in ongoing_project_statuses,
                    },
                    "archived": workspace["is_archived"],
                }

    # using a DRF serializer for now, so we've *some* schema definition
    level4_user = Level4AuthenticatedUser(
        data=dict(
            username=user.username,
            fullname=user.fullname,
            workspaces=workspaces,
            # note, we use a generic role check here rather than a permissions
            # as its currently a global role. In future, if output checking
            # permissions applies to different projects/orgs, we'll need to
            # list the explicit workspaces that the user has this permission
            # for.
            output_checker=has_role(user, OutputChecker),
        )
    )
    # we must validate this or DRF will refuse to serializer it.
    level4_user.is_valid()

    return level4_user


class Level4TokenAuthenticationAPI(APIView):
    authentication_classes = []

    class serializer_class(serializers.Serializer):
        user = serializers.CharField()
        token = serializers.CharField()

    def post(self, request):
        # Only allow requests from backend (this function raises the appropriate
        # exceptions)
        get_backend_from_token(request.headers.get("Authorization"))

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data

        try:
            # user can be username or email
            user = users.validate_login_token(data["user"], data["token"])
        except (
            User.DoesNotExist,
            users.TokenLoginException,
        ) as exc:
            logger.info(f"API Login with token failed for user {data['user']}: {exc}")
            trace.get_current_span().record_exception(exc)
            raise NotAuthenticated(str(exc))

        logger.info(f"User {user} logged in with login token via API")

        level4_user = build_level4_user(user)

        return Response(level4_user.data)


class Level4AuthorisationAPI(APIView):
    authentication_classes = []

    class serializer_class(serializers.Serializer):
        user = serializers.CharField()

    def post(self, request):
        # Only allow requests from backend (this function raises the appropriate
        # exceptions)
        get_backend_from_token(request.headers.get("Authorization"))

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data

        try:
            user = get_object_or_404(User, username=data["user"])
            users.validate_token_login_allowed(user)
        except users.TokenLoginException as exc:
            logger.info(f"User {data['user']} is not a valid Level 4 user")
            trace.get_current_span().record_exception(exc)
            raise NotAuthenticated(str(exc))

        logger.info(f"Provided authorization information for {user} via API")

        level4_user = build_level4_user(user)

        return Response(level4_user.data)
