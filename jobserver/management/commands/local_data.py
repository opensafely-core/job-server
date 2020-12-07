import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from jobserver.models import Job, JobRequest, User, Workspace


actions = [
    "run",
    "process",
    "hide",
    "leap",
    "science",
]


def request_1(workspace, user, now):
    """
    Succeeded JobRequest

    Each related Job finished without error.
    """
    request1 = JobRequest.objects.create(created_by=user, workspace=workspace)

    Job.objects.create(
        request=request1,
        workspace=workspace,
        action=random.choice(actions),
        started_at=now + timedelta(minutes=9),
        completed_at=now + timedelta(minutes=10),
    )
    Job.objects.create(
        request=request1,
        workspace=workspace,
        action=random.choice(actions),
        started_at=now + timedelta(minutes=7),
        completed_at=now + timedelta(minutes=8),
    )
    Job.objects.create(
        request=request1,
        workspace=workspace,
        action=random.choice(actions),
        started_at=now + timedelta(minutes=5),
        completed_at=now + timedelta(minutes=6),
    )
    Job.objects.create(
        request=request1,
        workspace=workspace,
        action=random.choice(actions),
        started_at=now + timedelta(minutes=3),
        completed_at=now + timedelta(minutes=4),
    )
    Job.objects.create(
        request=request1,
        workspace=workspace,
        action=random.choice(actions),
        started_at=now + timedelta(minutes=1),
        completed_at=now + timedelta(minutes=2),
    )


def request_2(workspace, user, now):
    """
    Running JobRequest

    One Job has succeeded, one is currently running, and one is pending.
    """
    request2 = JobRequest.objects.create(created_by=user, workspace=workspace)

    Job.objects.create(
        request=request2,
        workspace=workspace,
        action=random.choice(actions),
        started_at=now,
        completed_at=now + timedelta(minutes=1),
    )
    Job.objects.create(
        request=request2,
        workspace=workspace,
        action=random.choice(actions),
        started_at=now + timedelta(minutes=2),
    )
    Job.objects.create(
        request=request2, workspace=workspace, action=random.choice(actions)
    )


def request_3(workspace, user, now):
    """
    Failed JobRequest

    One Job succeeded, one failed, and the final one failed because the second
    one failed.
    """
    # JobRequest 3 - failed
    request3 = JobRequest.objects.create(created_by=user, workspace=workspace)

    Job.objects.create(
        request=request3,
        workspace=workspace,
        action=random.choice(actions),
        started_at=now + timedelta(minutes=3),
        completed_at=now + timedelta(minutes=19),
    )
    Job.objects.create(
        request=request3,
        workspace=workspace,
        action=random.choice(actions),
        status="failed",
    )
    Job.objects.create(
        request=request3,
        workspace=workspace,
        action=random.choice(actions),
        status="failed",
    )


def request_4(workspace, user, now):
    """
    Pending JobRequest

    All Jobs are Pending.
    """
    request4 = JobRequest.objects.create(created_by=user, workspace=workspace)

    Job.objects.create(
        request=request4,
        workspace=workspace,
        action=random.choice(actions),
    )
    Job.objects.create(
        request=request4,
        workspace=workspace,
        action=random.choice(actions),
    )


class Command(BaseCommand):
    def handle(self, *args, **options):
        Job.objects.all().delete()
        JobRequest.objects.all().delete()

        workspace, _ = Workspace.objects.get_or_create(
            name="Atlantis", repo="atlantis", branch="tauri"
        )

        george = User.objects.first()
        now = timezone.now() - timedelta(hours=1)

        request_1(workspace, george, now)
        request_2(workspace, george, now)
        request_3(workspace, george, now)
        request_4(workspace, george, now)
