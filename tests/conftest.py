import os
import textwrap

import pytest
import structlog
from django.conf import settings
from structlog.testing import LogCapture

import services.slack
from applications.form_specs import form_specs
from jobserver.authorization.roles import CoreDeveloper

from .factories import OrgFactory, OrgMembershipFactory, UserFactory
from .factories import applications as application_factories


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture
def api_rf():
    from rest_framework.test import APIRequestFactory

    return APIRequestFactory()


@pytest.fixture
def core_developer():
    return UserFactory(roles=[CoreDeveloper])


@pytest.fixture(name="log_output")
def fixture_log_output():
    return LogCapture()


@pytest.fixture(autouse=True)
def fixture_configure_structlog(log_output):
    structlog.configure(processors=[log_output])


@pytest.fixture(autouse=True)
def set_release_storage(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "RELEASE_STORAGE", tmp_path / "releases")


@pytest.fixture
def user():
    """
    Generate a User instance with useful things attached

    We almost always want a User to be part of an OpenSAFELY Org and have that
    Org tied to a GitHub Organisation.
    """
    org = OrgFactory(name="OpenSAFELY", slug="opensafely")
    user = UserFactory()

    # Make the User part of the Org
    OrgMembershipFactory(org=org, user=user)

    return user


@pytest.fixture
def complete_application():
    application = application_factories.ApplicationFactory()
    for form_spec in form_specs:
        factory_name = form_spec.model.__name__ + "Factory"
        factory = getattr(application_factories, factory_name)
        factory(application=application)
    return application


@pytest.fixture
def incomplete_application():
    application = application_factories.ApplicationFactory()
    for form_spec in form_specs[:10]:
        factory_name = form_spec.model.__name__ + "Factory"
        factory = getattr(application_factories, factory_name)
        factory(application=application)
    return application


slack_token = os.environ.get("SLACK_BOT_TOKEN")
slack_test_channel = os.environ.get("SLACK_TEST_CHANNEL")


@pytest.fixture
def slack_messages(monkeypatch, enable_network):
    messages = []

    actual_post = services.slack.post

    def post(text, channel):
        messages.append((text, channel))

        if slack_token and slack_test_channel:  # pragma: no cover
            actual_post(text, slack_test_channel)

    monkeypatch.setattr("services.slack.post", post)
    return messages


@pytest.fixture
def pipeline_config():
    """
    A miniminal, valid pipeline/project.yaml configuration
    """
    config = """
      version: 3

      expectations:
        population_size: 1000

      actions:
        generate_dataset:
          run: >
            databuilder:v0 generate_dataset
              --dataset-definition analysis/dataset_definition.py
              --dummy-data-file dummy_data.csv
              --output output/dataset.csv
          outputs:
            highly_sensitive:
              dataset: output/dataset.csv

    """
    return textwrap.dedent(config)
