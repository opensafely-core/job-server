from datetime import timedelta

import pytest
from django.utils import timezone

from jobserver.emails import send_finished_notification

from ..factories import JobFactory, JobRequestFactory, WorkspaceFactory


@pytest.mark.django_db
def test_send_finished_notification(mailoutbox):
    now = timezone.now()

    workspace = WorkspaceFactory(name="mailable-workspace")
    job_request = JobRequestFactory(workspace=workspace)
    job = JobFactory(
        job_request=job_request,
        action="run-serious-research",
        status="succeeded",
        status_message="test message",
        started_at=now - timedelta(minutes=480, seconds=52),
        completed_at=now,
    )

    send_finished_notification("test@example.com", job)

    m = mailoutbox[0]

    assert job.action in m.subject
    assert job.status in m.subject
    assert workspace.name in m.subject

    assert job.action in m.body
    assert job.status in m.body
    assert job.status_message in m.body
    assert str(job.runtime.total_seconds) in m.body

    assert list(m.to) == ["test@example.com"]
