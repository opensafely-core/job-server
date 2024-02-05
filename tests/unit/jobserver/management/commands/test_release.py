import csv
from io import StringIO

import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import call_command

from jobserver.models import Workspace

from .....factories import (
    BackendFactory,
    ProjectFactory,
    RepoFactory,
    UserFactory,
    WorkspaceFactory,
)


def assert_expected_output(stdout, expected_files, workspace):
    a, release_url, workspace_url = stdout.getvalue().splitlines()
    assert a == "Release created:"

    assert workspace_url.endswith(workspace.get_absolute_url())

    release = workspace.releases.get()
    assert release_url.endswith(release.get_absolute_url())

    release_files = release.files.order_by("name")

    assert release_files.count() == len(expected_files)

    for rf, ef in zip(release_files, expected_files):
        assert rf.path.endswith(ef.name)
        assert rf.name.endswith(ef.name)
        ef.read_text() == rf.absolute_path().read_text()


def prepare_release_files(release_dir):
    headers = ["a", "b", "c"]
    rows = [[1, 2, 3], [4, 5, 6]]
    files = []
    for row in rows:
        f = release_dir / f"{row[0]}.csv"
        with f.open("w") as of:
            writer = csv.writer(of)
            writer.writerow(headers)
            writer.writerow(row)
        files.append(f)
    return files


def test_release_command(tmp_path):
    release_dir = tmp_path / "test_release_comand"
    release_dir.mkdir()

    expected_files = prepare_release_files(release_dir)

    out = StringIO()
    err = StringIO()
    call_command("release", "-c", release_dir, stdout=out, stderr=err)
    workspace = Workspace.objects.get(name="test-workspace")

    assert_expected_output(out, expected_files, workspace)


def test_release_command_with_new_workspace(tmp_path):
    release_dir = tmp_path / "test_release_command_with_new_workspace"
    release_dir.mkdir()

    expected_files = prepare_release_files(release_dir)

    project = ProjectFactory()
    repo = RepoFactory(url="https://github.com/opensafely/test-repo")
    workspace = WorkspaceFactory(
        project=project, repo=repo, name=f"{project.slug}-workspace"
    )

    out = StringIO()
    err = StringIO()
    call_command(
        "release",
        release_dir,
        "-w",
        workspace.name,
        "-c",
        stdout=out,
        stderr=err,
    )

    assert not err.getvalue()
    assert_expected_output(out, expected_files, workspace)


def test_release_command_fails_with_missing_user(tmp_path):
    release_dir = tmp_path / "test_release_command_fails_with_missing_user"
    release_dir.mkdir()

    out = StringIO()
    err = StringIO()
    with pytest.raises(ObjectDoesNotExist):
        call_command(
            "release",
            release_dir,
            stdout=out,
            stderr=err,
        )


def test_release_command_fails_with_missing_workspace(tmp_path):
    release_dir = tmp_path / "test_release_command_fails_with_missing_workspace"
    release_dir.mkdir()

    user = UserFactory()

    out = StringIO()
    err = StringIO()
    with pytest.raises(ObjectDoesNotExist):
        call_command(
            "release",
            release_dir,
            "-u",
            user.username,
            stdout=out,
            stderr=err,
        )


def test_release_command_fails_with_missing_backend(tmp_path):
    release_dir = tmp_path / "test_release_command_fails_with_missing_backend"
    release_dir.mkdir()

    user = UserFactory()
    backend = BackendFactory()

    out = StringIO()
    err = StringIO()
    with pytest.raises(ObjectDoesNotExist):
        call_command(
            "release",
            release_dir,
            "-u",
            user.username,
            "-b",
            backend.slug,
            stdout=out,
            stderr=err,
        )
