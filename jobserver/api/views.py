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
        queryset = Job.objects.all().order_by("-created_at")
        qs_filter = {}
        if "started" in self.request.query_params:
            started_param = self.request.query_params.get("started", "False").lower()
            if started_param == "true":
                qs_filter["started"] = True
            elif started_param == "false":
                qs_filter["started"] = False
        if "repo" in self.request.query_params:
            qs_filter["repo"] = self.request.query_params["repo"]
        if "backend" in self.request.query_params:
            qs_filter["backend"] = self.request.query_params["backend"]
        if qs_filter:
            return queryset.filter(**qs_filter)
        else:
            return queryset.all()
