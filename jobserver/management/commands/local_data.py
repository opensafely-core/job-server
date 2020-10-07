import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from jobserver.models import Job, Workspace


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        Create 20 Jobs for each Status
        """

        actions = [
            "run",
            "process",
            "hide",
            "leap",
            "science",
        ]

        workspace, _ = Workspace.objects.get_or_create(
            name="Atlantis", repo="atlantis", branch="tauri"
        )

        now = timezone.now() - timedelta(hours=1)

        for _ in range(20):
            now = now + timedelta(minutes=1)

            # Completed
            Job.objects.create(
                workspace=workspace,
                action_id=random.choice(actions),
                started_at=now,
                completed_at=timezone.now(),
            )

            # Dependency Failed
            Job.objects.create(
                workspace=workspace, action_id=random.choice(actions), status_code=7
            )

            # Failed
            Job.objects.create(
                workspace=workspace, action_id=random.choice(actions), status_code=1
            )

            # In Progress
            Job.objects.create(
                workspace=workspace, action_id=random.choice(actions), started_at=now
            )

            # Pending
            Job.objects.create(workspace=workspace, action_id=random.choice(actions))
