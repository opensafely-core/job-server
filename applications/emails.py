from django.conf import settings
from furl import furl
from incuna_mail import send


def send_submitted_application_email(email, application):
    f = furl(settings.BASE_URL)
    f.path = application.get_absolute_url()

    context = {
        "url": f.url,
    }

    send(
        to=email,
        sender="notifications@jobs.opensafely.org",
        subject="Thank you for applying to use OpenSAFELY",
        template_name="applications/emails/submission_confirmation.txt",
        html_template_name="applications/emails/submission_confirmation.html",
        context=context,
    )
