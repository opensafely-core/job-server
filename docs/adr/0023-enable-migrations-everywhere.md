# Enable migrations everywhere

Date: 2024-08-27

## Status

Draft

## Context

Prior to this ADR, and with a single exception,
[migrations were disabled][1] for every context within which tests were executed.
Within these contexts,
pytest-django was configured to create a test database by inspecting all models.
The single exception was the `test` job of the `CI` GitHub action context.
Within this context,
pytest-django was configured to create a test database by calling Django's `migrate` management command.

[1]: https://pytest-django.readthedocs.io/en/latest/database.html#no-migrations-disable-django-migrations

Consequently, if a new migration *could* raise an exception,
then it *would* raise an exception only:

1. within the `test` job of the `CI` GitHub action context; and
1. if the code path that could raise an exception was followed.

[Data migrations][2] are more likely *not* to satisfy the above conditions,
because data migrations are more likely to contain code paths that are *not* followed.
For example, consider the following snippet from a data migration:

[2]: https://docs.djangoproject.com/en/5.1/topics/migrations/#data-migrations

```py
def forwards(apps, schema_editor):
    MyModel = apps.get_model("myapp", "MyModel")
    for my_model in MyModel.objects.all():
        # If there aren't any instances of MyModel,
        # then this code path won't be followed and
        # this exception won't be raised.
        my_model.my_field = "..."
        my_model.save()  # raises an exception
```

The `test` job of the `CI` GitHub action context creates, but doesn't populate, a test database.
Consequently, within this context and given the previous snippet from a data migration,
there wouldn't be any instances of `MyModel`,
so the code path wouldn't be followed and the exception wouldn't be raised.

If this wasn't confusing enough, even if the above conditions were satisfied,
then a new migration that raised an exception would cause every test in the test session to fail,
writing large amounts of text to stderr.
This is because pytest-django's [`django_db_setup`][3] fixture is called once at the beginning of every test session
(it has session scope).
In turn, it calls Django's `migrate` management command,
via Django's [`setup_databases`][4] function.
If a new migration raises an exception, however,
then `django_db_setup` will terminate abnormally
-- before pytest records that it was called, but after the test database is created --
and the current test in the test session will fail.
pytest, however, didn't record that `django_db_setup` was called,
so if there is another test in the test session, then `django_db_setup` is called *again*.
And *again*, `django_db_setup` will terminate abnormally and the next test in the test session will fail.

[3]: https://pytest-django.readthedocs.io/en/latest/database.html#django-db-setup
[4]: https://docs.djangoproject.com/en/5.1/topics/testing/advanced/#django.test.utils.setup_databases

Thankfully, because migrations run inside transactions,
a new migration that raises an exception won't leave the database in an inconsistent state,
should it be deployed.
Nevertheless, it's not surprising that migrations
-- especially data migrations --
can be very hard to reason about.

## Decision

**We will enable migrations for every context within which tests are executed.**
Doing so won't follow any new code paths,
but it will alert us to the most obvious errors, sooner.

**We will commit to running `python manage.py migrate` against a recent database dump**
when creating, and reviewing the creation of, a new migration.
Doing so will follow many new code paths,
and it will alert us to the less obvious errors, sooner.

**We will spike [django-test-migrations][5] when we next create a new data migration.**
There are several trade-offs associated with introducing django-test-migrations (or a similar dependency).
We should consider them in a spike, the outcome of which should be an ADR.

[5]: https://github.com/wemake-services/django-test-migrations

## Consequences

The decision won't alert us to all errors,
but it will alert us to many errors.

Enabling migrations for every context within which tests are executed may increase the time it takes to run test sessions.
Indeed, three warm test runs (`just test`) suggest that test runs take roughly 20s (22%) longer:
from roughly 1m30 to roughly 1m50.
We feel this cost is worth the benefit.
