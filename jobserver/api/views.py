from jobserver.api.models import Job
from jobserver.api.serializers import JobSerializer

from rest_framework import viewsets


class JobViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows jobs to be viewed or edited.
    """

    serializer_class = JobSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned jobs based on any `started` param
        """
        started = None
        queryset = Job.objects.all().order_by("-created_at")
        if "started" in self.request.query_params:
            started_param = self.request.query_params.get("started", "False").lower()
            if started_param == "true":
                started = True
            elif started_param == "false":
                started = False
        if started is not None:
            return queryset.filter(started=started)
        else:
            return queryset.all()
