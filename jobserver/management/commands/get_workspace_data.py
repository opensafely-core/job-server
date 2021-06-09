import csv

from django.core.management.base import BaseCommand
from django.db.models import Count

from jobserver.models import User, Workspace


class Command(BaseCommand):
    """
    A helper script to work out who is the most likely "primary" user for a
    Workspace.

    When mapping Workspaces to Projects most of the work is finding the
    relevant person to ask.  This script gets the number of JobRequests per
    User for each Workspace and dumps them to a CSV to work with.
    """

    def handle(self, *args, **options):
        workspaces = (
            Workspace.objects.annotate(jr_count=Count("job_requests"))
            .exclude(jr_count=0)
            .order_by("name")
        )

        with open("workspaces.csv", "w") as f:
            writer = csv.DictWriter(f, ["workspace", "users with counts"])
            writer.writeheader()

            for workspace in workspaces:
                users = (
                    User.objects.filter(job_requests__workspace=workspace)
                    .prefetch_related("job_requests")
                    .annotate(jr_count=Count("job_requests"))
                )

                users_and_counts = [
                    {
                        "count": user.jr_count,
                        "name": user.name,
                    }
                    for user in users
                ]

                # sort users by their count
                users_and_counts = sorted(
                    users_and_counts, key=lambda uc: uc["count"], reverse=True
                )

                # convert to strings
                users_with_counts = [
                    f"{u['name']} ({u['count']})" for u in users_and_counts
                ]

                user_with_counts = " | ".join(users_with_counts)

                writer.writerow(
                    {"workspace": workspace.name, "users with counts": user_with_counts}
                )
