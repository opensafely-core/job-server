from django.conf import settings
from furl import furl
from incuna_mail import send

from .models import User


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
        subject=f"{job.status}: [os {workspace_name}] {job.action}",
        template_name="emails/notify_finished.txt",
        context=context,
    )


def send_repo_signed_off_notification_to_researchers(repo):
    creators = User.objects.filter(workspaces__repo=repo)
    emails = [
        u.notifications_email if u.notifications_email else u.email for u in creators
    ]

    send(
        to="notifications@jobs.opensafely.org",
        bcc=emails,
        sender="notifications@jobs.opensafely.org",
        subject=f"Repo {repo.name} was signed off by {repo.researcher_signed_off_by.name}",
        template_name="emails/notify_researcher_repo_signed_off.txt",
        context={"repo": repo},
    )


def send_repo_signed_off_notification_to_staff(repo):
    numbers = [str(w.project.number) for w in repo.workspaces.all() if w.project.number]
    numbers = ",".join(numbers) if numbers else "X"
    subject = (
        f"[{numbers}] - Historic repo with outputs - sign off required {repo.name}"
    )

    staff_url = (furl(settings.BASE_URL) / repo.get_staff_url()).url

    send(
        to=["publications@opensafely.org"],
        sender="notifications@jobs.opensafely.org",
        subject=subject,
        template_name="emails/notify_staff_repo_signed_off.txt",
        context={"repo": repo, "staff_url": staff_url},
    )
