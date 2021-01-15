import pytest

from jobserver.emails import send_finished_notification

from ..factories import JobFactory, JobRequestFactory, WorkspaceFactory


@pytest.mark.django_db
def test_send_finished_notification(mailoutbox):
    workspace = WorkspaceFactory(name="mailable-workspace")
    job_request = JobRequestFactory(workspace=workspace)
    job = JobFactory(
        job_request=job_request,
        status="succeeded",
        status_message="test message",
    )

    send_finished_notification("test@example.com", job)

    m = mailoutbox[0]

    assert job.action in m.subject
    assert job.status in m.subject
    assert workspace.name in m.subject

    assert job.action in m.body
    assert job.status in m.body
    assert job.status_message in m.body

    assert list(m.to) == ["test@example.com"]
