import structlog
from django.http import FileResponse
from rest_framework import serializers
from rest_framework.exceptions import NotAuthenticated, NotFound, ValidationError
from rest_framework.generics import CreateAPIView
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.views import APIView
from slack_sdk.errors import SlackApiError

from jobserver.api import get_backend_from_token
from jobserver.models import Release, Workspace
from jobserver.releases import handle_release
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


class ReleaseUploadAPI(APIView):
    # DRF file upload does not use multipart, is just a simple byte stream
    parser_classes = [FileUploadParser]

    def put(self, request, workspace_name, release_hash):
        try:
            workspace = Workspace.objects.get(name=workspace_name)
        except Workspace.DoesNotExist:
            return Response(status=404)

        # authenticate and get backend
        backend = get_backend_from_token(request.headers.get("Authorization"))
        backend_user = request.headers.get("Backend-User", "").strip()
        if not backend_user:
            raise NotAuthenticated("Backend-User not valid")

        if "file" not in request.data:
            raise ValidationError({"detail": "No data uploaded"})

        upload = request.data["file"]
        release, created = handle_release(
            workspace, backend, backend_user, release_hash, upload
        )

        response = Response(status=201 if created else 303)
        response["Location"] = request.build_absolute_uri(release.get_absolute_url())
        response["Release-Id"] = release.id
        return response


def validate_release_access(request, release_hash):
    try:
        release = Release.objects.get(id=release_hash)
    except Release.DoesNotExist:
        raise NotFound(f"Release {release_hash} does not exist")

    # TODO: check if release is published
    if request.user.is_anonymous:
        raise NotAuthenticated("Invalid user or token")
    else:
        project = release.workspace.project
        if not project.members.filter(username=request.user.username).exists():
            raise NotAuthenticated(f"Invalid user or token for release {release_hash}")

    return release


class ReleaseIndexAPI(APIView):
    def get(self, request, release_hash):
        release = validate_release_access(request, release_hash)
        files = [v["name"] for v in release.files.values("name")]
        return Response(files)


class ReleaseFileAPI(APIView):
    def get(self, request, release_hash, filename):
        release = validate_release_access(request, release_hash)
        rfile = release.files.get(name=filename)

        handle = rfile.absolute_path()
        # check the file actually exists on disk
        if not handle.exists():
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
            response = FileResponse(handle.open("rb"))

        return response
