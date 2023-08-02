import pytest
from django.conf import settings
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from jobserver.models import PublishRequest, Snapshot
from jobserver.utils import set_from_qs
from tests.factories import (
    PublishRequestFactory,
    ReleaseFactory,
    ReleaseFileFactory,
    ReleaseFileReviewFactory,
    ReportFactory,
    SnapshotFactory,
    UserFactory,
    WorkspaceFactory,
)
from tests.utils import minutes_ago


def test_publishrequest_approve_configured_now():
    snapshot = SnapshotFactory()
    snapshot.files.add(*ReleaseFileFactory.create_batch(3))
    request = PublishRequestFactory(snapshot=snapshot)
    user = UserFactory()

    dt = minutes_ago(timezone.now(), 3)

    request.approve(user=user, now=dt)

    request.refresh_from_db()
    assert request.decision_at == dt


def test_publishrequest_approve_default_now(freezer):
    snapshot = SnapshotFactory()
    snapshot.files.add(*ReleaseFileFactory.create_batch(3))
    request = PublishRequestFactory(snapshot=snapshot)
    user = UserFactory()

    request.approve(user=user)

    request.refresh_from_db()
    assert request.decision_at == timezone.now()
    assert request.decision_by == user
    assert request.decision == PublishRequest.Decisions.APPROVED


def test_publishrequest_create_from_files_success():
    workspace = WorkspaceFactory()
    rfile = ReleaseFileFactory(workspace=workspace)
    user = UserFactory()

    request = PublishRequest.create_from_files(files=[rfile], user=user)

    assert request.created_by == user
    assert set_from_qs(request.snapshot.files.all()) == {rfile.pk}


def test_publishrequest_create_from_files_with_duplicate_files():
    workspace = WorkspaceFactory()
    rfile = ReleaseFileFactory(workspace=workspace)

    snapshot = SnapshotFactory(workspace=workspace)
    snapshot.files.add(rfile)

    user = UserFactory()

    publish_request = PublishRequest.create_from_files(files=[rfile], user=user)

    assert publish_request.snapshot == snapshot


def test_publishrequest_create_from_files_with_existing_publish_request():
    workspace = WorkspaceFactory()
    files = ReleaseFileFactory.create_batch(3, workspace=workspace)
    snapshot = SnapshotFactory(workspace=workspace)
    snapshot.files.set(files)
    user = UserFactory()

    publish_request = PublishRequestFactory(snapshot=snapshot, created_by=user)

    output = PublishRequest.create_from_files(files=files, user=user)

    assert output == publish_request


def test_publishrequest_create_from_files_with_existing_snapshot():
    workspace = WorkspaceFactory()
    files = ReleaseFileFactory.create_batch(3, workspace=workspace)

    snapshot1 = SnapshotFactory(workspace=workspace)
    snapshot1.files.set(files)

    snapshot2 = SnapshotFactory(workspace=workspace)
    snapshot2.files.set(files)

    with pytest.raises(Snapshot.MultipleObjectsReturned):
        PublishRequest.create_from_files(files=files, user=UserFactory())


def test_publishrequest_create_from_files_with_multiple_workspaces():
    user = UserFactory()

    rfiles = [
        ReleaseFileFactory(workspace=WorkspaceFactory()),
        ReleaseFileFactory(workspace=WorkspaceFactory()),
    ]

    with pytest.raises(PublishRequest.MultipleWorkspacesFound):
        PublishRequest.create_from_files(files=rfiles, user=user)


def test_publishrequest_create_from_report_success():
    report = ReportFactory()
    user = UserFactory()

    request = PublishRequest.create_from_report(report=report, user=user)

    assert request.created_by == user
    assert request.report == report
    assert request.updated_by == user


def test_publishrequest_get_approve_url(publish_request_with_report):
    url = publish_request_with_report.get_approve_url()

    assert url == reverse(
        "staff:publish-request-approve",
        kwargs={
            "pk": publish_request_with_report.report.pk,
            "publish_request_pk": publish_request_with_report.pk,
        },
    )


def test_publishrequest_get_reject_url(publish_request_with_report):
    url = publish_request_with_report.get_reject_url()

    assert url == reverse(
        "staff:publish-request-reject",
        kwargs={
            "pk": publish_request_with_report.report.pk,
            "publish_request_pk": publish_request_with_report.pk,
        },
    )


def test_publishrequest_is_approved():
    publish_request = PublishRequestFactory(
        decision=PublishRequest.Decisions.APPROVED,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
    )

    assert publish_request.is_approved


def test_publishrequest_is_pending():
    assert PublishRequestFactory().is_pending


def test_publishrequest_is_rejected():
    publish_request = PublishRequestFactory(
        decision=PublishRequest.Decisions.REJECTED,
        decision_at=timezone.now(),
        decision_by=UserFactory(),
    )

    assert publish_request.is_rejected


def test_publishrequest_reject(freezer):
    request = PublishRequestFactory()
    user = UserFactory()

    request.reject(user=user)

    request.refresh_from_db()
    assert request.decision_at == timezone.now()
    assert request.decision_by == user
    assert request.decision == PublishRequest.Decisions.REJECTED


def test_publishrequest_save():
    # a publish request with no report FK should work
    snapshot = SnapshotFactory()
    PublishRequestFactory(snapshot=snapshot)

    # a publish request with the wrong report should return an error
    report1 = ReportFactory()

    report2 = ReportFactory()
    snapshot = SnapshotFactory()
    snapshot.files.set([report2.release_file])

    with pytest.raises(PublishRequest.IncorrectReportError):
        PublishRequestFactory(snapshot=snapshot, report=report1)


def test_publishrequest_str():
    snapshot = SnapshotFactory()
    publish_request = PublishRequestFactory(snapshot=snapshot)

    assert str(publish_request) == f"Publish request for Snapshot={snapshot.pk}"


@pytest.mark.parametrize("field", ["created_at", "created_by"])
def test_release_created_check_constraint_missing_one(field):
    with pytest.raises(IntegrityError):
        ReleaseFactory(**{field: None})


def test_release_get_absolute_url():
    release = ReleaseFactory()

    url = release.get_absolute_url()

    assert url == reverse(
        "release-detail",
        kwargs={
            "project_slug": release.workspace.project.slug,
            "workspace_slug": release.workspace.name,
            "pk": release.id,
        },
    )


def test_release_get_api_url():
    release = ReleaseFactory()

    assert release.get_api_url() == f"/api/v2/releases/release/{release.id}"


def test_release_get_download_url():
    release = ReleaseFactory()

    url = release.get_download_url()

    assert url == reverse(
        "release-download",
        kwargs={
            "project_slug": release.workspace.project.slug,
            "workspace_slug": release.workspace.name,
            "pk": release.id,
        },
    )


def test_release_ulid():
    assert ReleaseFactory().ulid.timestamp


def test_releasefile_absolute_path(release):
    rfile = release.files.first()

    expected = (
        settings.RELEASE_STORAGE
        / release.workspace.name
        / "releases"
        / release.id
        / "file1.txt"
    )
    path = rfile.absolute_path()
    assert path == expected
    assert path.read_text()


@pytest.mark.parametrize("field", ["created_at", "created_by"])
def test_releasefile_created_check_constraint_missing_one(field):
    with pytest.raises(IntegrityError):
        ReleaseFileFactory(**{field: None})


def test_releasefile_constraints_deleted_at_and_deleted_by_both_set():
    ReleaseFileFactory(deleted_at=timezone.now(), deleted_by=UserFactory())


def test_releasefile_constraints_deleted_at_and_deleted_by_neither_set():
    ReleaseFileFactory(deleted_at=None, deleted_by=None)


@pytest.mark.django_db(transaction=True)
def test_releasefile_constraints_missing_deleted_at_or_deleted_by():
    with pytest.raises(IntegrityError):
        ReleaseFileFactory(deleted_at=None, deleted_by=UserFactory())

    with pytest.raises(IntegrityError):
        ReleaseFileFactory(deleted_at=timezone.now(), deleted_by=None)


def test_releasefile_format():
    size = 3.2 * 1024 * 1024  # 3.2Mb
    rfile = ReleaseFileFactory(name="important/research.html", size=size)

    assert f"{rfile:b}" == "3,355,443.2b"
    assert f"{rfile:Kb}" == "3,276.8Kb"
    assert f"{rfile:Mb}" == "3.2Mb"
    assert f"{rfile}".startswith("important/research.html")


def test_releasefile_get_absolute_url():
    rfile = ReleaseFileFactory(name="file1.txt")

    url = rfile.get_absolute_url()

    assert url == reverse(
        "release-detail",
        kwargs={
            "project_slug": rfile.release.workspace.project.slug,
            "workspace_slug": rfile.release.workspace.name,
            "pk": rfile.release.id,
            "path": rfile.name,
        },
    )


def test_releasefile_get_delete_url():
    rfile = ReleaseFileFactory()

    url = rfile.get_delete_url()

    assert url == reverse(
        "release-file-delete",
        kwargs={
            "project_slug": rfile.release.workspace.project.slug,
            "workspace_slug": rfile.release.workspace.name,
            "pk": rfile.release.id,
            "release_file_id": rfile.pk,
        },
    )


def test_releasefile_get_latest_url():
    rfile = ReleaseFileFactory(name="file1.txt")

    url = rfile.get_latest_url()

    assert url == reverse(
        "workspace-latest-outputs-detail",
        kwargs={
            "project_slug": rfile.release.workspace.project.slug,
            "workspace_slug": rfile.release.workspace.name,
            "path": f"{rfile.release.backend.slug}/{rfile.name}",
        },
    )


def test_releasefile_get_api_url_without_is_published():
    rfile = ReleaseFileFactory()

    url = rfile.get_api_url()

    assert url == reverse("api:release-file", kwargs={"file_id": rfile.id})


def test_releasefile_get_api_url_with_is_published():
    rfile = ReleaseFileFactory()

    # mirror the SnapshotAPI view setting this value on the ReleaseFile object.
    setattr(rfile, "is_published", True)

    url = rfile.get_api_url()

    assert url == reverse(
        "published-file",
        kwargs={
            "project_slug": rfile.workspace.project.slug,
            "workspace_slug": rfile.workspace.name,
            "file_id": rfile.id,
        },
    )


def test_releasefile_str():
    rfile = ReleaseFileFactory(id="12345", name="important/research.html")

    assert str(rfile) == "important/research.html (12345)"


def test_releasefile_ulid():
    assert ReleaseFileFactory().ulid.timestamp


@pytest.mark.parametrize("field", ["created_at", "created_by"])
def test_releasefilereview_created_check_constraint_missing_one(field):
    with pytest.raises(IntegrityError):
        ReleaseFileReviewFactory(**{field: None})


@pytest.mark.parametrize("field", ["created_at", "created_by"])
def test_snapshot_created_check_constraint_missing_one(field):
    with pytest.raises(IntegrityError):
        SnapshotFactory(**{field: None})


def test_snapshot_get_absolute_url():
    snapshot = SnapshotFactory()

    url = snapshot.get_absolute_url()

    assert url == reverse(
        "workspace-snapshot-detail",
        kwargs={
            "project_slug": snapshot.workspace.project.slug,
            "workspace_slug": snapshot.workspace.name,
            "pk": snapshot.pk,
        },
    )


def test_snapshot_get_api_url():
    snapshot = SnapshotFactory()

    url = snapshot.get_api_url()

    assert url == reverse(
        "api:snapshot",
        kwargs={
            "workspace_id": snapshot.workspace.name,
            "snapshot_id": snapshot.pk,
        },
    )


def test_snapshot_get_download_url():
    snapshot = SnapshotFactory()

    url = snapshot.get_download_url()

    assert url == reverse(
        "workspace-snapshot-download",
        kwargs={
            "project_slug": snapshot.workspace.project.slug,
            "workspace_slug": snapshot.workspace.name,
            "pk": snapshot.pk,
        },
    )


def test_snapshot_get_publish_api_url():
    snapshot = SnapshotFactory()

    url = snapshot.get_publish_api_url()

    assert url == reverse(
        "api:snapshot-publish",
        kwargs={
            "workspace_id": snapshot.workspace.name,
            "snapshot_id": snapshot.pk,
        },
    )


def test_snapshot_is_draft():
    assert SnapshotFactory().is_draft


def test_snapshot_is_published():
    snapshot = SnapshotFactory()

    PublishRequestFactory(
        snapshot=snapshot,
        decision_by=UserFactory(),
        decision_at=timezone.now(),
        decision=PublishRequest.Decisions.APPROVED,
    )

    assert snapshot.is_published


def test_snapshot_str():
    user = UserFactory()

    snapshot = SnapshotFactory(created_by=user)
    PublishRequestFactory(
        snapshot=snapshot,
        decision=PublishRequest.Decisions.APPROVED,
        decision_at=timezone.now(),
        decision_by=user,
    )
    assert str(snapshot) == f"Published Snapshot made by {user.username}"

    snapshot = SnapshotFactory(created_by=user)
    assert str(snapshot) == f"Draft Snapshot made by {user.username}"
