from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import connections, transaction
from faker import Faker


fake = Faker()

APPLICATIONS_TO_SCRUB = {
    "applications",
    "jobserver",
    "redirects",
}
"""Names of Django applications with models to be scrubbed."""

TABLES_TO_TRUNCATE = [
    # Session tokens should be kept secret and are not needed for local development.
    # They are also arguably personal data.
    "django_session",
    # All the social auth tables may contain tokens or personal data and they
    # are not needed for local development.
    "social_auth_association",
    "social_auth_code",
    "social_auth_partial",
    "social_auth_nonce",
    "social_auth_usersocialauth",
]
"""Names of Database tables to be truncated entirely."""


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

    def _truncate_tables(self, database_alias):
        connection = connections[database_alias]
        sql_list = connection.ops.sql_flush(
            no_style(), TABLES_TO_TRUNCATE, allow_cascade=False
        )

        self.stdout.write("Truncating tables")
        with connection.cursor() as cursor:
            for sql_query in sql_list:
                self.stdout.write(sql_query)
                cursor.execute(sql_query)
        self.stdout.write("Truncating tables complete")

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

            self._truncate_tables(database_alias)

        self.stdout.write("Committed transaction")
