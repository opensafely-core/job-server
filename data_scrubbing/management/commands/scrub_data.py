"""
Management command to scrub the database of sensitive data from selected fields.

See data scrubbing related ADRs for an overall description of the design of our
data scrubbing capability. See DEVELOPERS.md for what developers need to know to
obtain scrubbed and raw production database dumps for use in local development.
See the automated tooling that calls this module as a management command to
understand how this is used in production to generate the scrubbed dump.

You may need to understand this module if you want to change how data scrubbing
works.

You may also be reading this because you are adding a new model or model field.
In that case you need to add or update the DataScrubbing nested class on your
model, as explained below.

Data Scrubbing Configuration
============================

We identify which fields do and do not need scrubbing through the use of a
special nested class attached to each Django model in our applications. This
exhaustively lists all of the fields in that class and categorises them as
needing scrubbing or allowed to be left unchanged. This is exhaustive to help
ensure that we think about every field and make an active decision to allow it
or scrub it. An example class looks like this:


    class DataScrubbing:
        fields_to_scrub = {
            "email": fake_unique_email,
            "user_name": "Fake user name",
            "secret_token": None,
            "secret_token_expires_at": None,
            "special_key": get_random_key,
        }
        allowed_fields = frozenset(
            [
                "id",
                "created_at",
                "created_by",
                "foo",
                "qux",

            ]
        )

The class name must be DataScrubbing. It must have two attributes,
fields_to_scrub and allowed_fields, which must be a dict and a frozenset
respectively. It appears after field definitions, manager definitions, and
other "declarative" lines and just before the Meta nested class, or just before
any model methods if there is no Meta.

Classifying fields
------------------

The keys of fields_to_scrub correspond to the names of the model fields that
contain sensitive values. The values associated define how to scrub that field.
If the value is a generator object or a callable (such as a function) then it
will be invoked without arguments to produce values at data-scrubbing-time,
once per instance. Depending how you design the generator or callable, this can
be used to make values that satisfy certain constraints that your data has,
such as uniqueness. Otherwise, the value is used as a hardcoded value to be
assigned to all instances of that model. When data scrubbing is run, these
values are assigned to the model instances and saved to the database.

The keys of allowed_fields correspond to the other fields of the model that do
not need changing during data scrubbing because they do not contain sensitive
data.

You need to classify ForeignKeys on the model in which they are declared. That
is because the underlying database table has a column for the ForeignKey on the
side that declared it (but not in its target), and we need to decide whether to
scrub that. You do not need to add a corresponding entry in the target table,
as that reverse relation defined in Django does not correspond to a concrete
field stored in the target model's database table.

You do not need to classify ManyToManyFields on either related model, because
they are not concrete fields stored in either model's database table. They are
stored in a separate table. Instead, we can add a DataScrubbing class to the
through model. For example, on ProjectMembership for the ManyToManyField
relating Projects and Users.

Testing
-------

There is an automated integration test that will check that all fields are
included in exactly one of those data structures. It will try to provide
helpful output to hint which fields you need to do something with that can be
copied into the right part of your DataScrubbing and tailored to your case.
There is no automated test that tries to verify that the choices of data
scrubbing used are appropriate.

Otherwise, all of the above requirements are enforced by convention and
implicitly in the tests and command. There is no parent class for DataScrubbing.
We could add one if we want to enforce the structure more explicitly.


Sensitive Data - what is it ?
=============================

How do you decide what counts as sensitive data? We are thinking of two main
categories, so far, Personal Data and secrets.

First of all, err on the side of caution. If there is any doubt, scrub it. Gut
test: would it be bad if a developer laptop with that information on it were
compromised or lost?

If there is sensitive data that you think you need to allow for the purposes of
local development, discuss with your team if there is any way that you can
replace, simulate, or pseudonymise the data with a generator or callable. If we
do this, the rationale should be carefully documented in a comment in the
DataScrubbing.

The primary key ID in Job Server models should always be defined as an opaque
integer so should be allowed. Timestamps such as created_at are usually okay.

Personal Data
-------------

Personal Data corresponds more or less to the definitions from UK GDPR and Data
Protection Acts, which are binding on us when we process Personal Data; we must
limit data processing to that which is necessary for the purposes we are
processing it for (UK GDPR Article 5(1)(c)). So when we create a dump for use
in local development, it should not contain Personal Data, unless there is a
clear purpose to including it. If you think that may be your case, discuss it
with your team and team lead.

Personal Data means any information relating to an identified or identifiable
natural person. Typically for us that means things like people's names,
addresses, phone numbers, job roles, education or other history. It can also
include any kind of text about the individual. For that reason, free-text fields
that users can supply the data for in a form should probably always be
scrubbed, as users may include personal data there about themselves or others.

Further reading:

https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/
https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/personal-information-what-is-it/what-is-personal-data/what-is-personal-data/


Secrets
-------

Secrets are any kind of token, key, password or other information that ought to
be kept confidential and not revealed, usually for security reasons. Metadata
about those secrets such as expiry times should probably also be scrubbed to be
cautious.

Truncation
==========

Some tables we want to remove all the entries from, either because we decided
that they have no value for local development, or because they contain
sensitive data that we cannot easily scrub while maintaining validity. These
can also include third-party-package or Django-defined models that we cannot
currently configure with the DataScrubbing mechanism.

Add the Postgres database table name for those to TABLES_TO_TRUNCATE.

It is okay to include a table that does have a DataScrubbing configuration in
TABLES_TO_TRUNCATE. It will be scrubbed then truncated, ending up empty.

The DataScrubbing exhaustiveness tests currently act on all models in whole
applications, so if a model you want to truncate is in an application that we
scrub, it will need to be in TABLES_TO_TRUNCATE and have a DataScrubbing
defined on the model.
"""

import inspect
from datetime import datetime

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


def get_fake_unique_email():
    """Generator function for a "fairly unique" fake e-mail address string.

    It embeds the start time of the generator and an loop counter so should be
    unique within-process (assuming no threading) and between consecutive runs
    triggered by humans, but is not globally unique. In practice we only expect
    one data scrubbing process at a time, so this should be sufficient to avoid
    hitting uniqueness constraints.

    Example fake e-mail generated: '260716073644_1@example.com'."""
    start_time_str = datetime.now().strftime("%y%m%d%H%M%S")
    count = 0

    while True:
        count += 1
        yield f"{start_time_str}_{count}@example.com"


fake_unique_email = get_fake_unique_email()
"""Generator for a "fairly unique" fake e-mail address string.

This is in this module as a variable so that multiple places can share this and
avoid repeats, and because this module is where the mechanisms for data
scrubbing are defined."""


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
                        if inspect.isgenerator(fake_value):
                            value = next(fake_value)
                        elif callable(fake_value):
                            value = fake_value()
                        else:
                            value = fake_value
                        setattr(obj, attr_name, value)
                    obj.save(using=database_alias, update_fields=field_names)
                    count += 1

                self.stdout.write(
                    f"Scrubbed {count} {model.__name__} records from fields: {', '.join(field_names)}"
                )

            self._truncate_tables(database_alias)

        self.stdout.write("Committed transaction")
