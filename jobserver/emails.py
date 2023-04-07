from django.conf import settings
from django.urls import reverse
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
        html_template_name="emails/notify_finished.html",
        context=context,
    )


def send_github_login_email(user):
    context = {
        "url": furl(settings.BASE_URL) / reverse("login"),
    }

    send(
        to=user.email,
        subject="Log into OpenSAFELY",
        sender="notifications@jobs.opensafely.org",
        reply_to=["OpenSAFELY Team <team@opensafely.org>"],
        template_name="emails/login_via_github.txt",
        html_template_name="emails/login_via_github.html",
        context=context,
    )


def send_login_email(user, login_url, timeout_minutes):
    url = furl(settings.BASE_URL) / login_url

    context = {
        "timeout_minutes": timeout_minutes,
        "url": url,
    }

    send(
        to=user.email,
        subject="Log into OpenSAFELY",
        sender="notifications@jobs.opensafely.org",
        reply_to=["OpenSAFELY Team <team@opensafely.org>"],
        template_name="emails/login.txt",
        html_template_name="emails/login.html",
        context=context,
    )


def send_repo_signed_off_notification_to_researchers(repo):
    creators = User.objects.filter(workspaces__repo=repo)
    emails = [u.notifications_email for u in creators]

    send(
        to="notifications@jobs.opensafely.org",
        bcc=emails,
        sender="notifications@jobs.opensafely.org",
        subject=f"Repo {repo.name} was signed off by {repo.researcher_signed_off_by.name}",
        template_name="emails/notify_researcher_repo_signed_off.txt",
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

    send(
        to=["publications@opensafely.org"],
        sender="notifications@jobs.opensafely.org",
        subject=subject,
        template_name="emails/notify_staff_repo_signed_off.txt",
        html_template_name="emails/notify_staff_repo_signed_off.html",
        context={"repo": repo, "staff_url": staff_url},
    )


def send_welcome_email(user):
    login_url = furl(settings.BASE_URL) / reverse("login")

    context = {
        "domain": settings.BASE_URL,
        "name": user.name,
        "url": login_url,
    }

    send(
        to=user.email,
        subject="Welcome to OpenSAFELY",
        sender="notifications@jobs.opensafely.org",
        reply_to=["OpenSAFELY Team <team@opensafely.org>"],
        template_name="emails/welcome.txt",
        html_template_name="emails/welcome.html",
        context=context,
    )


def send_token_login_generated_email(user):
    send(
        to=user.notifications_email,
        subject="New OpenSAFELY login token generated",
        sender="notifications@jobs.opensafely.org",
        reply_to=["OpenSAFELY Team <team@opensafely.org>"],
        template_name="emails/login_token_generated.txt",
        html_template_name="emails/login_token_generated.html",
    )


def send_token_login_used_email(user):
    send(
        to=user.notifications_email,
        subject="OpenSAFELY account login with token",
        sender="notifications@jobs.opensafely.org",
        reply_to=["OpenSAFELY Team <team@opensafely.org>"],
        template_name="emails/login_token_used.txt",
        html_template_name="emails/login_token_used.html",
    )
