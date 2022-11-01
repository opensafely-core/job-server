from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from jobserver.emails import (
    send_finished_notification,
    send_researcher_repo_signed_off_notification,
)

from ...factories import (
    JobFactory,
    JobRequestFactory,
    RepoFactory,
    UserFactory,
    WorkspaceFactory,
)


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
    assert job.get_absolute_url() in m.body
    assert settings.BASE_URL in m.body

    assert list(m.to) == ["test@example.com"]


def test_send_researcher_repo_signed_off_notification(mailoutbox):
    user1 = UserFactory()
    user2 = UserFactory()
    user3 = UserFactory()

    repo = RepoFactory(
        researcher_signed_off_at=timezone.now(),
        researcher_signed_off_by=user1,
    )
    WorkspaceFactory(created_by=user1, repo=repo)
    WorkspaceFactory(created_by=user2, repo=repo)
    WorkspaceFactory(created_by=user3, repo=repo)

    send_researcher_repo_signed_off_notification(repo)

    m = mailoutbox[0]

    assert list(m.to) == []
    assert list(m.bcc) == [user1.email, user2.email, user3.email]
