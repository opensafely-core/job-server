from django.conf import settings
from furl import furl
from incuna_mail import send


def send_finished_notification(email, job):
    f = furl(settings.BASE_URL)
    f.path = job.get_absolute_url()

    workspace_name = job.job_request.workspace.name

    context = {
        "action": job.action,
        "elapsed_time": job.runtime.total_seconds if job.runtime else None,
        "status": job.status,
        "status_message": job.status_message,
        "url": f.url,
        "workspace": workspace_name,
    }

    send(
        to=email,
        sender="notifications@jobs.opensafely.org",
        subject=f"[os {workspace_name}] {job.action} {job.status}",
        template_name="emails/notify_finished.txt",
        context=context,
    )


def send_project_invite_email(email, project, invite):
    f = furl(settings.BASE_URL)
    f.path = project.get_absolute_url()

    context = {
        "inviter_name": invite.created_by.name,
        "project_name": project.name,
        "url": f.url,
    }

    send(
        to=email,
        sender="notifications@jobs.opensafely.org",
        subject=f"OpenSAFELY Project Invite from {invite.created_by.name} to {project.name}",
        template_name="emails/project_invite.txt",
        context=context,
    )
