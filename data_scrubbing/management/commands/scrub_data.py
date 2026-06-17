from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from faker import Faker


fake = Faker()


class Command(BaseCommand):
    """Management command to scrub sensitive fields"""

    help = "Scrub sensitive data from selected fields"

    def add_arguments(self, parser):
        options = list(settings.DATABASES.keys())
        parser.add_argument(
            "database_alias",
            help=f"Alias of database to scrub, options: {options}",
        )
        parser.add_argument(
            "--i-am-sure",
            action="store_true",
            dest="i_am_sure",
            help="Must be set to scrub the default database",
        )

    def handle(self, *args, **kwargs):
        database_alias = kwargs["database_alias"]
        if database_alias == "default" and not kwargs["i_am_sure"]:
            raise CommandError("Use --i-am-sure flag to run against default database")

        models = {model for model in apps.get_app_config("jobserver").get_models()}
        models |= {model for model in apps.get_app_config("applications").get_models()}
        with transaction.atomic(using=database_alias):
            for model in models:
                data_scrubbing = getattr(model, "DataScrubbing", None)
                if data_scrubbing is None:
                    continue
                scrub_fields = getattr(data_scrubbing, "fields_to_scrub", None)
                if not scrub_fields:
                    continue
                field_names = scrub_fields.keys()

                objs = model.objects.using(database_alias).all().iterator()
                count = 0
                for obj in objs:
                    for attr_name, fake_value in scrub_fields.items():
                        value = fake_value() if callable(fake_value) else fake_value
                        setattr(obj, attr_name, value)
                    obj.save(using=database_alias, update_fields=field_names)
                    count += 1

                self.stdout.write(
                    f"Scrubbed {count} {model.__name__} records from fields: {', '.join(field_names)}"
                )
        self.stdout.write("Committed scrubbing transaction")
