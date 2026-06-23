from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from faker import Faker


fake = Faker()

APPLICATIONS_TO_SCRUB = {
    "applications",
    "jobserver",
    "redirects",
}
"Names of Django applications with models to be scrubbed."


def get_scrubbed_models():
    "Accumulate set of Django model classes to be scrubbed."
    scrubbed_models = set()
    for application in APPLICATIONS_TO_SCRUB:
        scrubbed_models |= {
            model for model in apps.get_app_config(application).get_models()
        }
    return scrubbed_models


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

        with transaction.atomic(using=database_alias):
            for model in get_scrubbed_models():
                # Find fields to scrub, if any.
                data_scrubbing = getattr(model, "DataScrubbing", None)
                if data_scrubbing is None:
                    continue
                scrub_fields = getattr(data_scrubbing, "fields_to_scrub", None)
                if not scrub_fields:
                    continue
                field_names = scrub_fields.keys()

                # Iterate per-object updating and saving scrubbed fields.
                # Many small queries in the transaction but avoids either holding
                # whole tables in memory or chunking bulk updates.
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
