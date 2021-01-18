from incuna_mail import send


def send_finished_notification(email, job):
    workspace_name = job.job_request.workspace.name

    context = {
        "action": job.action,
        "elapsed_time": "",
        "status": job.status,
        "status_message": job.status_message,
        "url": job.get_absolute_url(),
        "workspace": workspace_name,
    }

    send(
        to=email,
        sender="notificaitons@jobs.opensafely.org",
        subject=f"[os {workspace_name}] {job.action} {job.status}",
        template_name="emails/notify_finished.txt",
        context=context,
    )
