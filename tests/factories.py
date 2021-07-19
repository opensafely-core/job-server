import hashlib
import io
from dataclasses import dataclass
from datetime import datetime

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
    Snapshot,
    Stats,
    User,
    Workspace,
)


class BackendFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Backend

    name = factory.Sequence(lambda n: f"backend-{n}")


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


class SnapshotFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Snapshot

    created_by = factory.SubFactory("tests.factories.UserFactory")
    workspace = factory.SubFactory("tests.factories.WorkspaceFactory")


@dataclass
class ReleaseUpload:
    filename: str
    contents: bytes
    filehash: str = ""

    def __post_init__(self):
        if not self.filehash:  # pragma: no cover
            self.filehash = hashlib.sha256(self.contents).hexdigest()

    @property
    def stream(self):
        return io.BytesIO(self.contents)


def ReleaseUploadsFactory(files):
    if isinstance(files, list):
        files = {f: f.encode("utf8") for f in files}

    return [ReleaseUpload(filename=k, contents=v) for k, v in files.items()]


def ReleaseFactory(
    uploads, uploaded=True, workspace=None, backend=None, created_by=None, **kwargs
):
    """Factory for Release objects.

    You must supply a list of ReleaseUpload's as the first argument. If you
    want an 'empty' release, pass uploaded=False.

    Not a Factory Boy factory, as the need for files on disk and
    file hashes to be known ahead of time to create valid objects
    just does not work with Factory Boy.
    """

    created_by = created_by or UserFactory()
    backend = backend or BackendFactory()
    workspace = workspace or WorkspaceFactory()
    release = releases.create_release(
        workspace=workspace,
        backend=backend,
        created_by=created_by,
        requested_files={u.filename: u.filehash for u in uploads},
        **kwargs,
    )

    # create the ReleaseFile objects
    if uploaded:
        for upload in uploads:
            ReleaseFileFactory(
                upload,
                release=release,
                backend=backend,
                workspace=workspace,
                created_by=created_by,
            )

    return release


def ReleaseFileFactory(
    upload, release=None, created_by=None, workspace=None, backend=None, **kwargs
):
    """Factory for ReleaseFile objects.

    You must supply a ReleaseUpload as the first argument.

    Not a Factory Boy factory, as the need for files on disk and
    file hashes to be known ahead of time to create valid objects
    just does not work with Factory Boy.
    """
    created_by = created_by or UserFactory()
    backend = backend or BackendFactory()
    workspace = workspace or WorkspaceFactory()
    release = release or ReleaseFactory(
        [upload],
        uploaded=False,
        workspace=workspace,
        backend=backend,
        created_by=created_by,
    )

    # use the business logic to actually create it.
    return releases.handle_file_upload(
        release,
        backend,
        created_by,
        upload.stream,
        upload.filename,
    )


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
