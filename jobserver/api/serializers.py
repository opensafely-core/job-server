from jobserver.api.models import Job
from jobserver.api.models import JobOutput
from rest_framework import serializers


class JobOutputSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = JobOutput
        fields = ["name", "location", "privacy_level"]


class JobSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="jobs-detail")
    outputs = JobOutputSerializer(many=True, required=False)

    class Meta:
        model = Job
        fields = [
            "url",
            "repo",
            "backend",
            "db",
            "branch",
            "started",
            "operation",
            "status_code",
            "status_message",
            "outputs",
            "created_at",
            "started_at",
            "completed_at",
            "callback_url",
        ]
        read_only_fields = ["created_at", "started_at", "completed_at"]

    def create(self, validated_data):
        outputs_data = validated_data.pop("outputs", [])
        job = Job.objects.create(**validated_data)
        for output_data in outputs_data:
            JobOutput.objects.create(job=job, **output_data)
        return job

    def update(self, instance, validated_data):
        outputs_data = validated_data.pop("outputs", [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        for output_data in outputs_data:
            instance.outputs.update_or_create(**output_data)
        instance.save()
        return instance
