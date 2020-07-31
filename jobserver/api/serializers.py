from jobserver.api.models import Job
from rest_framework import serializers


class JobSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="jobs-detail")

    class Meta:
        model = Job
        fields = [
            "url",
            "repo",
            "backend",
            "db",
            "tag",
            "started",
            "operation",
            "status_code",
            "status_message",
            "output_bucket",
            "created_at",
            "started_at",
            "completed_at",
            "callback_url",
        ]
        read_only_fields = ["created_at", "started_at", "completed_at"]
