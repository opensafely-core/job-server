from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker


fake = Faker()


class Command(BaseCommand):
    """Management command to scrub sensitive fields"""

    help = "Scrub sensitive data from selected fields"

    def handle(self, *args, **kwargs):
        models = {model for model in apps.get_app_config("jobserver").get_models()}
        models |= {model for model in apps.get_app_config("applications").get_models()}
        with transaction.atomic():
            for model in models:
                data_scrubbing = getattr(model, "DataScrubbing", None)
                if data_scrubbing is None:
                    continue
                scrub_fields = getattr(data_scrubbing, "fields_to_scrub", None)
                if not scrub_fields:
                    continue
                field_names = scrub_fields.keys()

                objs = model.objects.all().iterator()
                count = 0
                for obj in objs:
                    for attr_name, fake_value in scrub_fields.items():
                        value = fake_value() if callable(fake_value) else fake_value
                        setattr(obj, attr_name, value)
                    obj.save(update_fields=field_names)
                    count += 1

                self.stdout.write(
                    f"Scrubbed {count} {model.__name__} records from fields: {', '.join(field_names)}"
                )
        self.stdout.write("Committed scrubbing transaction")
