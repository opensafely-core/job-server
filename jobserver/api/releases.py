import cgi

import structlog
from django.db import transaction
from django.db.models import Value
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import NotAuthenticated, ParseError, ValidationError
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.parsers import FileUploadParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from jobserver import releases, slacks
from jobserver.api import get_backend_from_token
from jobserver.authorization import has_permission
from jobserver.models import Release, ReleaseFile, Snapshot, User, Workspace
from jobserver.releases import serve_file
from jobserver.utils import set_from_qs


logger = structlog.get_logger(__name__)


class ReleaseNotificationAPICreate(CreateAPIView):
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
    if not has_permission(user, "release_file_upload", project=workspace.project):
        raise NotAuthenticated

    return backend, user


def validate_release_access(request, workspace):
    """Validate this request can access releases for this workspace.

    This validation uses a User PAT OR Django's regular User auth.
    """
    auth_header = request.headers.get("Authorization")
    if User.is_valid_pat(auth_header):
        return

    if request.user.is_anonymous:
        raise NotAuthenticated("Invalid user or token")

    if not has_permission(request.user, "release_file_view", project=workspace.project):
        raise NotAuthenticated(f"Invalid user or token for workspace {workspace.name}")


def validate_snapshot_access(request, snapshot):
    """
    Validate this request can access this snapshot.

    This validation uses Django's regular User auth.
    """
    if snapshot.published_at:
        return

    if request.user.is_anonymous:
        raise NotAuthenticated("Invalid user or token")

    if not has_permission(
        request.user, "release_file_view", project=snapshot.workspace.project
    ):
        raise NotAuthenticated(f"Invalid user or token for snapshot pk={snapshot.pk}")


def generate_index(files):
    """Generate a JSON list of files as expected by the SPA."""

    def get_size(rfile):
        try:
            return rfile.absolute_path().stat().st_size
        except FileNotFoundError:  # pragma: no cover
            return None

    return dict(
        files=[
            dict(
                name=name,
                id=rfile.pk,
                url=rfile.get_api_url(),
                user=rfile.created_by.username,
                date=rfile.created_at.isoformat(),
                sha256=rfile.filehash,
                size=get_size(rfile),
                is_deleted=rfile.deleted_at or not rfile.absolute_path().exists(),
                backend=rfile.release.backend.name,
            )
            for name, rfile in files.items()
        ],
    )


class ReleaseWorkspaceAPI(APIView):
    """Listing current files and creating new Releases for a workspace."""

    parsers = [JSONParser]

    class FilesSerializer(serializers.Serializer):
        files = serializers.DictField(child=serializers.CharField())

    def post(self, request, workspace_name):
        """Create a new Release for this workspace."""
        workspace = get_object_or_404(Workspace, name=workspace_name)
        backend, user = validate_upload_access(request, workspace)

        # parse the requested files
        serializer = self.FilesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        files = serializer.validated_data["files"]

        try:
            release = releases.create_release(workspace, backend, user, files)
        except releases.ReleaseFileAlreadyExists as exc:
            raise ValidationError({"detail": str(exc)})

        slacks.notify_release_created(release)

        response = Response(status=201)
        response["Location"] = request.build_absolute_uri(release.get_api_url())
        response["Release-Id"] = release.id
        return response

    def get(self, request, workspace_name):
        """List the most recent versions of files for the Workspace."""
        workspace = get_object_or_404(Workspace, name=workspace_name)
        validate_release_access(request, workspace)
        files = releases.workspace_files(workspace)
        return Response(generate_index(files))


class ReleaseAPI(APIView):
    # DRF file upload does not use multipart, is just a simple byte stream
    parser_classes = [FileUploadParser]

    def post(self, request, release_id):
        """Upload a file for this Release.

        File must be listed in Release.requested_files, and the hash must match.
        """
        release = get_object_or_404(Release, id=release_id)
        backend, user = validate_upload_access(request, release.workspace)

        try:
            upload = request.data["file"]
        except KeyError:
            raise ValidationError({"detail": "No data uploaded"})

        # DRF validates and parses the Content-Disposition header, but sadly
        # strips any directory paths from the filename. We need those paths, so
        # we need to reparse the header to get them.
        _, params = cgi.parse_header(request.headers["Content-Disposition"])
        filename = params["filename"]

        if filename not in release.requested_files:
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
        except releases.ReleaseFileAlreadyExists as exc:
            raise ValidationError({"detail": str(exc)})

        slacks.notify_release_file_uploaded(rfile)

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
    def get(self, request, file_id):
        """Return the content of a specific ReleaseFile"""
        rfile = get_object_or_404(ReleaseFile, id=file_id)
        validate_release_access(request, rfile.workspace)
        return serve_file(request, rfile)


class SnapshotAPI(APIView):
    def get(self, request, *args, **kwargs):
        """A list of files for this Snapshot."""
        snapshot = get_object_or_404(
            Snapshot,
            workspace__name=self.kwargs["workspace_id"],
            pk=self.kwargs["snapshot_id"],
        )

        # grab whether the Snapshot has been published so we can annotate a
        # static value to each ReleaseFile in the query below.
        is_published = snapshot.published_at is not None

        validate_snapshot_access(request, snapshot)
        files = {
            f.name: f
            for f in snapshot.files.select_related(
                "created_by",
                "release",
                "release__backend",
                "workspace",
                "workspace__project",
                "workspace__project__org",
            ).annotate(is_published=Value(is_published))
        }

        return Response(generate_index(files))


class SnapshotCreateAPI(APIView):
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
            request.user, "snapshot_create", project=workspace.project
        ):
            raise NotAuthenticated

        file_ids = set(data["file_ids"])
        files = ReleaseFile.objects.filter(pk__in=file_ids)

        rfile_ids = set_from_qs(files)
        snapshot_ids = [set_from_qs(s.files.all()) for s in workspace.snapshots.all()]
        if rfile_ids in snapshot_ids:
            msg = (
                "A release with the current files already exists, please use that one."
            )
            raise ParseError(msg)

        if missing := file_ids - set_from_qs(files):
            raise ParseError(f"Unknown file IDs: {', '.join(missing)}")

        snapshot = Snapshot.objects.create(created_by=request.user, workspace=workspace)
        snapshot.files.set(files)

        return Response({"url": snapshot.get_absolute_url()}, status=201)


class SnapshotPublishAPI(APIView):
    def post(self, request, *args, **kwargs):
        snapshot = get_object_or_404(
            Snapshot,
            workspace__name=self.kwargs["workspace_id"],
            pk=self.kwargs["snapshot_id"],
        )

        if not has_permission(
            request.user, "snapshot_publish", project=snapshot.workspace.project
        ):
            raise NotAuthenticated

        if snapshot.published_at:
            # The Snapshot has already been published, don't lose the original
            # information.
            return Response()

        snapshot.published_at = timezone.now()
        snapshot.published_by = request.user
        snapshot.save()

        return Response()


class WorkspaceStatusAPI(RetrieveAPIView):
    lookup_field = "name"
    lookup_url_kwarg = "workspace_id"
    queryset = Workspace.objects.all()

    class serializer_class(serializers.Serializer):
        uses_new_release_flow = serializers.BooleanField()
