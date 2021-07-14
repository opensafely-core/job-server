import structlog
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import NotAuthenticated, NotFound, ValidationError
from rest_framework.generics import CreateAPIView
from rest_framework.parsers import FileUploadParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from slack_sdk.errors import SlackApiError

from jobserver import releases
from jobserver.api import get_backend_from_token
from jobserver.authorization import has_permission
from jobserver.models import Release, User, Workspace
from services.slack import client as slack_client


logger = structlog.get_logger(__name__)


class ReleaseNotificationAPICreate(CreateAPIView):
    class serializer_class(serializers.Serializer):
        created_by = serializers.CharField()
        path = serializers.CharField()

    def initial(self, request, *args, **kwargs):
        token = request.META.get("HTTP_AUTHORIZATION")

        # require auth for all requests
        get_backend_from_token(token)

        return super().initial(request, *args, **kwargs)

    def perform_create(self, serializer):
        data = serializer.data

        message = f"{data['created_by']} released outputs from {data['path']}"
        try:
            slack_client.chat_postMessage(channel="opensafely-outputs", text=message)
        except SlackApiError:
            # log and don't block the response
            logger.exception("Failed to notify slack")


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

    # TODO: check user permissions
    return backend, user


def validate_release_access(request, workspace):
    """Validate this request can access releases for this workspace.

    This validation uses Django's regular User auth.
    """
    # TODO: check if release is published
    if request.user.is_anonymous:
        raise NotAuthenticated("Invalid user or token")

    if not has_permission(request.user, "view_release_file", project=workspace.project):
        raise NotAuthenticated(f"Invalid user or token for workspace {workspace.name}")


def generate_index(files):
    """Generate a JSON list of files as expected by the SPA."""
    return dict(
        files=[dict(name=k, url=v.get_api_url()) for k, v in files.items()],
    )


class ReleaseIndexAPI(APIView):
    def get(self, request, release_id):
        """A list of files for this Release."""
        release = get_object_or_404(Release, id=release_id)
        validate_release_access(request, release.workspace)
        files = {f.name: f for f in release.files.all()}
        return Response(generate_index(files))


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

        release = releases.create_release(workspace, backend, user, files)

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


class ReleaseFileAPI(APIView):
    # DRF file upload does not use multipart, is just a simple byte stream
    parser_classes = [FileUploadParser]

    def put(self, request, release_id, filename):
        """Upload a file for this Release.

        File must be listed in Release.requested_files, and the hash must match.
        """
        release = get_object_or_404(Release, id=release_id)

        if filename not in release.requested_files:
            raise NotFound

        backend, user = validate_upload_access(request, release.workspace)

        # ensure this is being released from the same backend as the Release
        # was created from
        if release.backend != backend:
            raise ValidationError(
                {
                    "detail": f"Release is from backend {release.backend.name} not {backend.name}"
                }
            )

        if "file" not in request.data:
            raise ValidationError({"detail": "No data uploaded"})

        releases.handle_file_upload(
            release, backend, user, request.data["file"], filename
        )

        return Response(status=200)

    def get(self, request, release_id, filename):
        """Return the content of a specific ReleaseFile"""
        release = get_object_or_404(Release, id=release_id)
        validate_release_access(request, release.workspace)
        rfile = release.files.get(name=filename)
        return serve_file(request, rfile)


def serve_file(request, rfile):
    """Serve a ReleaseFile as the response.

    If Releases-Redirect header is set, use nginx's X-Accel-Redirect to serve
    response. Else just serve the bytes directly (for dev).
    """
    path = rfile.absolute_path()
    # check the file actually exists on disk
    if not path.exists():
        raise NotFound

    internal_redirect = request.headers.get("Releases-Redirect")
    if internal_redirect:
        # we're behind nginx, so use X-Accel-Redirect to serve the file
        # from nginx, relative to RELEASES_STORAGE.
        response = Response()
        response.headers["X-Accel-Redirect"] = f"{internal_redirect}/{rfile.path}"
    else:
        # serve directly from django in dev use regular django response to
        # bypass DRFs renderer framework and just serve bytes
        response = FileResponse(path.open("rb"))

    return response
