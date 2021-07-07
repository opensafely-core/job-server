import io
import json
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import factory
import factory.fuzzy
from django.utils import timezone
from pytz import utc
from social_django.models import UserSocialAuth

from jobserver import releases
from jobserver.models import (
    Backend,
    BackendMembership,
    Job,
    JobRequest,
    Org,
    OrgMembership,
    Project,
    ProjectInvitation,
    ProjectMembership,
    ResearcherRegistration,
    Stats,
    User,
    Workspace,
)


class BackendFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Backend

    name = factory.Sequence(lambda n: f"Backend {n}")


class BackendMembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BackendMembership

    backend = factory.SubFactory("tests.factories.BackendFactory")
    user = factory.SubFactory("tests.factories.UserFactory")

    created_by = factory.SubFactory("tests.factories.UserFactory")


class JobFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Job

    job_request = factory.SubFactory("tests.factories.JobRequestFactory")

    identifier = factory.Sequence(lambda n: f"identifier-{n}")

    updated_at = factory.fuzzy.FuzzyDateTime(datetime(2020, 1, 1, tzinfo=timezone.utc))


class JobRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = JobRequest

    backend = factory.SubFactory("tests.factories.BackendFactory")
    created_by = factory.SubFactory("tests.factories.UserFactory")
    workspace = factory.SubFactory("tests.factories.WorkspaceFactory")

    requested_actions = []


class OrgFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Org

    name = factory.Sequence(lambda n: f"Organisation {n}")
    slug = factory.Sequence(lambda n: f"organisation-{n}")

    github_orgs = ["opensafely"]


class OrgMembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrgMembership

    org = factory.SubFactory("tests.factories.OrgFactory")
    user = factory.SubFactory("tests.factories.UserFactory")


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    org = factory.SubFactory("tests.factories.OrgFactory")

    name = factory.Sequence(lambda n: f"Project {n}")
    slug = factory.Sequence(lambda n: f"project-{n}")
    proposed_start_date = factory.fuzzy.FuzzyDateTime(
        datetime(2020, 1, 1, tzinfo=timezone.utc)
    )


class ProjectInvitationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProjectInvitation

    project = factory.SubFactory("tests.factories.ProjectFactory")
    user = factory.SubFactory("tests.factories.UserFactory")


class ProjectMembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProjectMembership

    project = factory.SubFactory("tests.factories.ProjectFactory")
    user = factory.SubFactory("tests.factories.UserFactory")


DEFAULT_MANIFEST = {"workspace": "workspace", "repo": "repo"}
DEFAULT_FILES = {"file.txt": "test"}


class ReleaseUploadFactory:
    """A zip bytestream with valid hash."""

    def __init__(
        self, files=DEFAULT_FILES, manifest=DEFAULT_MANIFEST, raw_manifest=None
    ):
        self.zip = io.BytesIO()
        with TemporaryDirectory() as d:
            tmp = Path(d)

            for path, contents in files.items():
                (tmp / path).write_text(contents)

            # raw_manifest allows us to write bad json for testing
            # setting manifest=None means we do not write a manifest
            if raw_manifest is None and manifest:
                raw_manifest = json.dumps(manifest)

            if raw_manifest:
                path = tmp / "metadata" / "manifest.json"
                path.parent.mkdir()
                path.write_text(raw_manifest)

            self.hash, self.files = releases.hash_files(tmp)

            with ZipFile(self.zip, "w") as zf:
                for f in self.files:
                    zf.write(tmp / f, arcname=str(f))

        self.zip.seek(0)


def ReleaseFactory(
    files=None,
    manifest=None,
    raw_manifest=None,
    workspace=None,
    backend=None,
    backend_user="user",
    created_at=None,
):
    """Factory for Release objects.

    Release has attributes that depend on its file contents, namely id,
    upload_dir and files. It also requires the associated filesystem state to
    exist.

    This makes it difficult to fit into how DjangoModelFactory works, so we
    implement our own Factory, that quacks like a DjangoModelFactory.

    It returns a Release object, but we create it manually.
    """

    if files is None:
        files = DEFAULT_FILES

    # files can be a list of files or a dict.
    # If it is a list, we default the file contents to be the name of the file.
    # If it is a dict, we use the values as content.
    if isinstance(files, list):
        files = {f: f for f in files}  # pragma: no cover

    manifest = manifest or DEFAULT_MANIFEST
    workspace = workspace or WorkspaceFactory()
    backend = backend or BackendFactory()

    # create an upload, so we know the release_hash ahead of time.
    upload = ReleaseUploadFactory(files, manifest, raw_manifest)

    release, _ = releases.handle_release(
        workspace, backend, backend_user, upload.hash, upload.zip
    )

    if created_at is not None:
        release.created_at = created_at
        release.save()

    return release


class ResearcherRegistrationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ResearcherRegistration

    user = factory.SubFactory("tests.factories.UserFactory")


class StatsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Stats

    backend = factory.SubFactory("tests.factories.BackendFactory")

    api_last_seen = factory.Faker("date_time", tzinfo=utc)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user-{n}")
    email = factory.Sequence(lambda n: f"user-{n}@example.com")
    notifications_email = factory.Sequence(lambda n: f"user-{n}@example.com")


class UserSocialAuthFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserSocialAuth

    user = factory.SubFactory("tests.factories.UserFactory")


class WorkspaceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Workspace

    project = factory.SubFactory("tests.factories.ProjectFactory")

    name = factory.Sequence(lambda n: f"workspace-{n}")
    repo = factory.Sequence(lambda n: "http://example.com/org-{n}/repo-{n}")
