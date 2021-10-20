from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Command to print the number of rows in each table

    This is a quick script to enable some extra checking in the postgres
    migration and can go away after that.
    """

    def handle(self, *args, **options):
        counts = []
        for _, app in apps.app_configs.items():
            for model in app.get_models():
                counts.append(
                    {
                        "name": model.__name__,
                        "count": model.objects.count(),
                    }
                )

        counts = sorted(counts, key=lambda c: c["name"])
        for model in counts:
            print(f"{model['name']:33} | {model['count']}")
