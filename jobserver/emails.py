from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from furl import furl

from .models import User


def send_html_email(
    to,
    from_email,
    subject,
    text_template_name,
    html_template_name,
    context=None,
    bcc=None,
    reply_to=None,
):
    """Send an HTML e-mail with a text fallback rendered from templates."""
    email = EmailMultiAlternatives(
        to=[to],
        reply_to=reply_to or None,
        bcc=bcc or None,
        from_email=from_email,
        subject=subject,
        body=render_to_string(text_template_name, context or {}),
    )
    email.attach_alternative(
        render_to_string(html_template_name, context or {}), "text/html"
    )
    email.send()


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

    send_html_email(
        to=email,
        from_email="notifications@jobs.opensafely.org",
        subject=f"{job.status}: [os {workspace_name}] {job.action}",
        text_template_name="emails/notify_finished.txt",
        html_template_name="emails/notify_finished.html",
        context=context,
    )


def send_repo_signed_off_notification_to_researchers(repo):
    creators = User.objects.filter(workspaces__repo=repo)
    emails = [u.email for u in creators]

    send_html_email(
        to="notifications@jobs.opensafely.org",
        bcc=emails,
        from_email="notifications@jobs.opensafely.org",
        subject=f"Repo {repo.name} was signed off by {repo.researcher_signed_off_by.name}",
        text_template_name="emails/notify_researcher_repo_signed_off.txt",
        html_template_name="emails/notify_researcher_repo_signed_off.html",
        context={"repo": repo},
    )


def send_repo_signed_off_notification_to_staff(repo):
    numbers = [str(w.project.number) for w in repo.workspaces.all() if w.project.number]
    numbers = ",".join(numbers) if numbers else "X"
    subject = (
        f"[{numbers}] - Historic repo with outputs - sign off required {repo.name}"
    )

    staff_url = (furl(settings.BASE_URL) / repo.get_staff_url()).url

    send_html_email(
        to="publications@opensafely.org",
        from_email="notifications@jobs.opensafely.org",
        subject=subject,
        text_template_name="emails/notify_staff_repo_signed_off.txt",
        html_template_name="emails/notify_staff_repo_signed_off.html",
        context={"repo": repo, "staff_url": staff_url},
    )


def send_token_login_generated_email(user):
    send_html_email(
        to=user.email,
        subject="New OpenSAFELY login token generated",
        from_email="notifications@jobs.opensafely.org",
        reply_to=["OpenSAFELY Team <team@opensafely.org>"],
        text_template_name="emails/login_token_generated.txt",
        html_template_name="emails/login_token_generated.html",
    )


def send_token_login_used_email(user):
    send_html_email(
        to=user.email,
        subject="OpenSAFELY account login with token",
        from_email="notifications@jobs.opensafely.org",
        reply_to=["OpenSAFELY Team <team@opensafely.org>"],
        text_template_name="emails/login_token_used.txt",
        html_template_name="emails/login_token_used.html",
    )
