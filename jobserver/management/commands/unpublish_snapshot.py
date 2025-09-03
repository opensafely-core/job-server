from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from jobserver.models import Snapshot


class Command(BaseCommand):
    help = (
        "Retrospectively reject the most recent approved request to publish a snapshot"
    )

    def add_arguments(self, parser):
        parser.add_argument("snapshot_id", type=int, help="The ID of the snapshot")
        parser.add_argument(
            "username",
            help="The username of the user who will retrospectively reject the request",
        )

    def handle(self, *args, **kwargs):
        snapshot_id = kwargs["snapshot_id"]
        username = kwargs["username"]

        try:
            snapshot = Snapshot.objects.get(pk=snapshot_id)
        except Snapshot.DoesNotExist:
            raise CommandError(f"Snapshot '{snapshot_id}' does not exist")

        User = get_user_model()
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' does not exist")

        if not snapshot.is_published:
            raise CommandError(f"Snapshot '{snapshot.pk}' is not published")

        most_recent_publish_request = snapshot.publish_requests.order_by(
            "created_at"
        ).last()

        self.stdout.write(
            f"User '{user.username}' is about to reject the most recent approved request to publish snapshot '{snapshot.pk}'"
        )
        most_recent_publish_request.reject(user=user)
        self.stdout.write(
            f"User '{user.username}' has rejected the most recent approved request to publish snapshot '{snapshot.pk}'"
        )
