from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from jobserver.api.models import Job
from jobserver.api.models import JobOutput
from jobserver.api.models import Workspace


class JobOutputAdmin(admin.ModelAdmin):
    model = JobOutput


class JobInline(admin.TabularInline):
    model = Job
    readonly_fields = (
        "started",
        "status_code",
        "status_message",
        "output_paths",
        "created_at",
        "started_at",
        "completed_at",
        "callback_url",
        "needed_by",
    )
    extra = 1
    show_change_link = 1

    def output_paths(self, obj):
        return ", ".join([x.location for x in obj.outputs.all()])

    # return ", ".join([1, 2])


class WorkspaceAdmin(admin.ModelAdmin):
    inlines = [
        JobInline,
    ]


admin.site.register(Workspace, WorkspaceAdmin)
admin.site.register(JobOutput, JobOutputAdmin)
