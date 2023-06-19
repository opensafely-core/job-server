from django.conf import settings
from django.urls import reverse
from furl import furl
from incuna_mail import send


def send_report_uploaded_notification(analysis_request):
    analysis_request_url = furl(settings.BASE_URL) / analysis_request.get_absolute_url()

    context = {
        "name": analysis_request.created_by.name,
        "title": analysis_request.title,
        "url": analysis_request_url,
    }

    send(
        to=analysis_request.created_by.email,
        sender="notifications@jobs.opensafely.org",
        subject="Your OpenSAFELY Interactive report is ready to view",
        template_name="emails/notify_report_uploaded.txt",
        html_template_name="emails/notify_report_uploaded.html",
        context=context,
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
