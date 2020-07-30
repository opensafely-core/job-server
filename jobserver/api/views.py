from jobserver.api.models import Job
from jobserver.api.serializers import JobSerializer

from rest_framework import viewsets


class JobViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows jobs to be viewed or edited.
    """

    queryset = Job.objects.all().order_by("-created_at")
    serializer_class = JobSerializer
    filterset_fields = ("started", "repo", "backend", "db", "tag", "operation")
