from django.conf import settings
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
        to=analysis_request.created_by.notifications_email,
        sender="notifications@jobs.opensafely.org",
        subject="Your OpenSAFELY Interactive report is ready to view",
        template_name="emails/notify_report_uploaded.txt",
        context=context,
    )
