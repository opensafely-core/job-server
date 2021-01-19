from incuna_mail import send


def send_finished_notification(email, job, job_url):
    workspace_name = job.job_request.workspace.name

    context = {
        "action": job.action,
        "elapsed_time": job.runtime.total_seconds,
        "status": job.status,
        "status_message": job.status_message,
        "url": job_url,
        "workspace": workspace_name,
    }

    send(
        to=email,
        sender="notifications@jobs.opensafely.org",
        subject=f"[os {workspace_name}] {job.action} {job.status}",
        template_name="emails/notify_finished.txt",
        context=context,
    )
