from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Job, JobOutput, Workspace


class JobOutputSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = JobOutput
        fields = ["location"]


class WorkspaceSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="workspaces-detail")
    owner = serializers.CharField(source="created_by.username", allow_null=True)

    class Meta:
        model = Workspace
        fields = [
            "id",
            "url",
            "name",
            "repo",
            "branch",
            "db",
            "owner",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class JobShimSerializer(serializers.Serializer):
    """
    Shim to bridge the gap between job-runner and job-server

    job-server has grown a JobRequest model to group it's Jobs.  However,
    changing job-runner to support this is a time-costly set of changes.  In
    the iterim this Serializer keeps the API interface job-runner expects,
    while translating fields/operations to the correct fields and models in
    job-server.
    """

    url = serializers.HyperlinkedIdentityField(view_name="jobs-detail")
    pk = serializers.IntegerField(read_only=True)
    backend = serializers.CharField(source="job_request.backend")
    started = serializers.BooleanField(default=False)
    force_run = serializers.BooleanField(default=False)
    force_run_dependencies = serializers.BooleanField(
        source="job_request.force_run_dependencies", default=False
    )
    action_id = serializers.CharField()
    status_code = serializers.IntegerField(allow_null=True, required=False)
    status_message = serializers.CharField(allow_null=True, required=False)
    outputs = JobOutputSerializer(many=True, required=False)
    needed_by_id = serializers.IntegerField(allow_null=True)
    workspace = WorkspaceSerializer(read_only=True, source="job_request.workspace")
    workspace_id = serializers.IntegerField(
        source="job_request.workspace_id", required=False
    )
    created_at = serializers.DateTimeField(read_only=True)
    started_at = serializers.DateTimeField(read_only=True)
    completed_at = serializers.DateTimeField(read_only=True)
    callback_url = serializers.CharField(
        source="job_request.callback_url", allow_null=True, required=False
    )

    def create(self, validated_data):
        # walk the dep links until we reach the leaf Job, which we expect to
        # have been created by job-server.  We can get a JobRequest from this
        # to attach new Jobs to.
        try:
            dependency = Job.objects.get(pk=validated_data["needed_by_id"])
        except Job.DoesNotExist:
            raise ValidationError("needed_by_id must be a valid Job ID")

        while dependency.needed_by is not None:
            dependency = dependency.needed_by

        job_request = dependency.job_request

        # remove the job_request key since the local job_request value is
        # going to replace any possible values here.
        # Note: This field is added by DRF travelling field sources which point
        # to the related job_request instance (eg source=job_request.backend)
        validated_data.pop("job_request", None)

        outputs = validated_data.pop("outputs", [])

        job = Job.objects.create(job_request=job_request, **validated_data)

        JobOutput.objects.bulk_create(
            JobOutput(job=job, location=output) for output in outputs
        )

        return job

    def update(self, instance, validated_data):
        outputs_data = validated_data.pop("outputs", [])

        # ensure job_request data isn't updated
        # Note: This field is added by DRF travelling field sources which point
        # to the related job_request instance (eg source=job_request.backend)
        validated_data.pop("job_request", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if instance.outputs.count() and outputs_data:
            raise ValidationError("You can only set outputs for a job once")

        for output_data in outputs_data:
            instance.outputs.create(location=output_data["location"])

        instance.save()
        return instance


class JobWithInlineWorkspaceSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="jobs-detail")
    outputs = JobOutputSerializer(many=True, required=False)
    workspace = WorkspaceSerializer()

    class Meta:
        model = Job
        fields = [
            "url",
            "backend",
            "db",
            "started",
            "action_id",
            "status_code",
            "status_message",
            "outputs",
            "workspace",
            "created_at",
            "started_at",
            "completed_at",
            "callback_url",
        ]
        read_only_fields = fields
