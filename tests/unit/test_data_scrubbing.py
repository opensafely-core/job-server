from django.apps import apps

from data_scrubbing.management.commands.scrub_data import APPLICATIONS_TO_SCRUB


def test_applications_to_scrub():
    """Test that all configured applications that have models are listed in
    either APPLICATIONS_TO_SCRUB or specifically allowed as hardcoded in this
    test.

    Exceptions should be truncated in scrub_data, or verified as not containing
    sensitive data.

    This is intended to catch the case where a whole new app with models is
    added in future, either through a new third-party package, or an app that
    we define. In that case, we should decide how to scrub it, either through
    truncation or DataScrubbing.
    """
    apps_with_models = {
        app_name for app_name in apps.app_configs if apps.app_configs[app_name].models
    }
    apps_confirmed_as_not_needing_scrubbing = frozenset(
        [
            # social django models are included in TABLES_TO_TRUNCATE
            "social_django",
            # django.contrib.auth by default would contain user data, in
            # auth_user, that would need to be scrubbed. But we use our own
            # custom User model in jobserver instead, and have confirmed that
            # there is nothing that needs scrubbing left in auth_* tables. But
            # it does need to be present for our User model and social_django
            # to work.
            "auth",
            # django.contrib.contenttypes tracks metadata about models, not
            # individual instances, so does not need scrubbing
            "contenttypes",
            # sessions models are included in TABLES_TO_TRUNCATE
            "sessions",
        ]
    )

    assert apps_with_models == apps_confirmed_as_not_needing_scrubbing.union(
        APPLICATIONS_TO_SCRUB
    ), (
        "All apps with models must be listed in APPLICATIONS_TO_SCRUB or apps_confirmed_as_not_needing_scrubbing"
    )
