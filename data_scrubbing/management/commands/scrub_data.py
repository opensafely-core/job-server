from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import OperationalError
from faker import Faker


fake = Faker()


class Command(BaseCommand):
    """Management command to scrub sensitive fields"""

    help = "Scrub sensitive data from selected fields"

    def handle(self, *args, **kwargs):
        try:
            self.scrub_data()
        except OperationalError as error:
            raise CommandError(
                "Could not connect to the database. "
                "Before running this command, make sure PostgreSQL is running. "
                "If using Docker, start it with `just docker/db`."
            ) from error

    def scrub_data(self):
        models = {model for model in apps.get_app_config("jobserver").get_models()}
        models |= {model for model in apps.get_app_config("applications").get_models()}

        for model in models:
            data_scrubbing = getattr(model, "DataScrubbing", None)
            if data_scrubbing is None:
                continue
            scrub_fields = getattr(data_scrubbing, "fields_to_scrub", None)
            if not scrub_fields:
                continue

            objs = list(model.objects.all())
            for obj in objs:
                for attr_name, fake_value in scrub_fields.items():
                    value = fake_value() if callable(fake_value) else fake_value
                    setattr(obj, attr_name, value)

            field_names = scrub_fields.keys()
            model.objects.bulk_update(objs, field_names)
            self.stdout.write(
                f"Scrubbed {len(objs)} {model.__name__} records from fields: {', '.join(field_names)}"
            )
