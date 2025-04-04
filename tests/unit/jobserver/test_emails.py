from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from jobserver.emails import (
    send_finished_notification,
    send_repo_signed_off_notification_to_researchers,
    send_repo_signed_off_notification_to_staff,
)

from ...factories import (
    JobFactory,
    JobRequestFactory,
    ProjectFactory,
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
    text_content = m.body
    html_content = m.alternatives[0][0]

    assert job.action in m.subject
    assert job.status in m.subject
    assert workspace.name in m.subject

    assert list(m.to) == ["test@example.com"]

    assert job.action in text_content
    assert job.action in html_content
    assert job.status in text_content
    assert job.status in html_content
    assert job.status_message in text_content
    assert job.status_message in html_content
    assert str(job.runtime.total_seconds) in text_content
    assert str(job.runtime.total_seconds) in html_content
    assert job.get_absolute_url() in text_content
    assert job.get_absolute_url() in html_content
    assert settings.BASE_URL in text_content
    assert settings.BASE_URL in html_content


def test_send_repo_signed_off_notification_to_researchers(mailoutbox):
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

    send_repo_signed_off_notification_to_researchers(repo)

    m = mailoutbox[0]
    text_content = m.body
    html_content = m.alternatives[0][0]

    assert list(m.to) == ["notifications@jobs.opensafely.org"]
    assert set(m.bcc) == {user1.email, user2.email, user3.email}

    assert repo.name in text_content
    assert repo.name in html_content
    assert repo.researcher_signed_off_by.fullname in text_content
    assert repo.researcher_signed_off_by.fullname in html_content


def test_send_repo_signed_off_notification_to_staff(mailoutbox):
    project1 = ProjectFactory(number=7)
    project2 = ProjectFactory(number=42)
    repo = RepoFactory(
        researcher_signed_off_at=timezone.now(),
        researcher_signed_off_by=UserFactory(),
    )
    WorkspaceFactory(project=project1, repo=repo)
    WorkspaceFactory(project=project2, repo=repo)

    send_repo_signed_off_notification_to_staff(repo)

    m = mailoutbox[0]
    text_content = m.body
    html_content = m.alternatives[0][0]

    assert list(m.to) == ["publications@opensafely.org"]
    assert "7,42" in m.subject

    assert repo.name in text_content
    assert repo.name in html_content
    assert repo.researcher_signed_off_by.fullname in text_content
    assert repo.researcher_signed_off_by.fullname in html_content
    assert repo.get_staff_url() in text_content
    assert repo.get_staff_url() in html_content
