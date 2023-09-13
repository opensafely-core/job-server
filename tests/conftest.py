import hashlib
import os
import random
import string
from pathlib import Path

import patchy
import pytest
import structlog
from attrs import define
from django.conf import settings
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.core.handlers.wsgi import WSGIRequest
from django.test import RequestFactory
from django.utils import timezone
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from structlog.testing import LogCapture

import services.slack
from applications.form_specs import form_specs
from jobserver.authorization.roles import CoreDeveloper

from .factories import (
    BackendFactory,
    BackendMembershipFactory,
    OrgFactory,
    OrgMembershipFactory,
    PublishRequestFactory,
    ReleaseFactory,
    ReleaseFileFactory,
    ReportFactory,
    SnapshotFactory,
    UserFactory,
    UserSocialAuthFactory,
)
from .factories import applications as application_factories


# set up tracing for tests
provider = TracerProvider()
trace.set_tracer_provider(provider)
test_exporter = InMemorySpanExporter()
provider.add_span_processor(SimpleSpanProcessor(test_exporter))


def get_trace():
    """Return all spans traced during this test."""
    return test_exporter.get_finished_spans()  # pragma: no cover


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture(scope="session", autouse=True)
def make_unordered_queries_randomly_ordered():
    """
    Patch Django’s ORM to randomly order all queries without a specified
    order.

    This discovers problems where code expects a given order but the
    database doesn’t guarantee one.

    https://adamj.eu/tech/2023/07/04/django-test-random-order-querysets/
    """
    from django.db.models.sql.compiler import SQLCompiler

    patchy.patch(
        SQLCompiler._order_by_pairs,  # type: ignore[attr-defined]
        """\
        @@ -9,7 +9,7 @@
                 ordering = meta.ordering
                 self._meta_ordering = ordering
             else:
        -        ordering = []
        +        ordering = ["?"]
             if self.query.standard_ordering:
                 default_order, _ = ORDER_DIR["ASC"]
             else:
        """,
    )


@pytest.fixture(autouse=True)
def clear_all_traces():
    test_exporter.clear()


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
    for form_spec in form_specs[:11]:
        factory_name = form_spec.model.__name__ + "Factory"
        factory = getattr(application_factories, factory_name)
        factory(application=application)
    return application


@pytest.fixture
def build_release(build_release_path):
    def func(names, **kwargs):
        requested_files = [{"name": n} for n in names]
        release = ReleaseFactory(requested_files=requested_files, **kwargs)

        build_release_path(release)

        return release

    return func


@pytest.fixture
def build_release_with_files(build_release, build_release_file):
    """Build a Release and generate some files for the given names"""

    def func(names, **kwargs):
        release = build_release(names, **kwargs)

        for name in names:
            build_release_file(release, name)

        return release

    return func


@pytest.fixture
def build_release_file(file_content):
    """
    Build a ReleaseFile

    Given a Release instance and a filename create both the ReleaseFile object
    and the on-disk file with random content from the file_content fixture.
    """

    def func(release, name):
        # build a relative path for the file
        path = Path(release.workspace.name) / "releases" / str(release.id) / name

        rfile = ReleaseFileFactory(
            release=release,
            workspace=release.workspace,
            name=name,
            path=path,
            filehash=hashlib.sha256(file_content).hexdigest(),
            size=len(file_content),
            uploaded_at=timezone.now(),
        )

        # write the file to disk
        rfile.absolute_path().write_bytes(file_content)

        return rfile

    return func


@pytest.fixture
def build_release_path(tmp_path):
    """Build the path and directories for a Release directory"""

    def func(release):
        path = (
            tmp_path
            / "releases"
            / release.workspace.name
            / "releases"
            / str(release.id)
        )
        path.mkdir(parents=True)

        return path

    return func


@pytest.fixture
def file_content():
    """Generate random file content ready for writing to disk"""
    content = "".join(random.choice(string.ascii_letters) for i in range(10))
    return content.encode("utf-8")


@pytest.fixture
def release(build_release_with_files):
    """Generate a Release instance with both a ReleaseFile and on-disk file"""
    return build_release_with_files(["file1.txt"])


slack_token = os.environ.get("SLACK_BOT_TOKEN")
slack_test_channel = os.environ.get("SLACK_TEST_CHANNEL")


@pytest.fixture
def slack_messages(monkeypatch, enable_network):
    """A mailoutbox style fixture for slack messages"""
    messages = []

    actual_post = services.slack.post

    def post(text, channel):
        messages.append((text, channel))

        if slack_token and slack_test_channel:  # pragma: no cover
            actual_post(text, slack_test_channel)

    monkeypatch.setattr("services.slack.post", post)
    return messages


class MessagesRequestFactory(RequestFactory):
    def request(self, **request):
        request = WSGIRequest(self._base_environ(**request))
        request.session = SessionStore()
        messages = FallbackStorage(request)
        request._messages = messages
        return request


@pytest.fixture
def rf_messages():
    return MessagesRequestFactory()


@pytest.fixture
def token_login_user():
    user = UserFactory()
    backend = BackendFactory()
    UserSocialAuthFactory(user=user)
    BackendMembershipFactory(user=user, backend=backend)
    return user


@pytest.fixture
def github_api():
    class CapturingGitHubAPI:
        issues = []

        def create_issue(self, **kwargs):
            @define
            class Issue:
                org: str
                repo: str
                title: str
                body: str
                labels: list[str]

            # capture all the values so they can interrogated later
            self.issues.append(Issue(**kwargs))

            return {
                "html_url": "http://example.com",
            }

    return CapturingGitHubAPI()


@pytest.fixture
def publish_request_with_report():
    rfile = ReleaseFileFactory()
    snapshot = SnapshotFactory()
    snapshot.files.set([rfile])

    report = ReportFactory(release_file=rfile)

    return PublishRequestFactory(report=report, snapshot=snapshot)
