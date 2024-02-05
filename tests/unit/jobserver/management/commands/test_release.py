import csv
from io import StringIO

from django.core.management import call_command

from jobserver.models import Workspace


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

    assert not err.getvalue()
    a, release_url, workspace_url = out.getvalue().splitlines()
    assert a == "Release created:"

    workspace = Workspace.objects.get(name="test-workspace")
    assert workspace_url.endswith(workspace.get_absolute_url())

    release = workspace.releases.get()
    assert release_url.endswith(release.get_absolute_url())

    release_files = release.files.order_by("name")

    assert release_files.count() == 2

    for rf, ef in zip(release_files, expected_files):
        assert rf.path.endswith(ef.name)
        assert rf.name.endswith(ef.name)
        ef.read_text() == rf.absolute_path().read_text()
