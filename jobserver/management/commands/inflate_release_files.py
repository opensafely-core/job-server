"""
Create files on disk for ReleaseFiles missing them

When we pull database dumps from production they won't bring down the files
related to ReleaseFiles.  However this makes working with the file viewer
harder since all links are effectively broken.  This command will generate
files for a variety of extensions with semi-useful junk data, eg a CSV file
with rows and columns.

Each make_* function is given a ReleaseFile instance and is free to
implement the creation of files as it sees fit.
"""

import csv
import json

from django.core.management.base import BaseCommand

from ...models import ReleaseFile


def make_csv(release_file):
    with release_file.absolute_path().open("w") as f:
        columns = ["id", "created_at", "workspace_name", "release_id"]
        writer = csv.DictWriter(f, columns)

        writer.writeheader()
        for _ in range(100):  # add 100 rows (randomly chosen number)
            writer.writerow(
                {
                    "id": release_file.pk,
                    "created_at": release_file.created_at.isoformat(),
                    "workspace_name": release_file.workspace.name,
                    "release_id": release_file.release.pk,
                }
            )


def make_html(release_file):
    template = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

    <title>Generated Page</title>
  </head>
  <body>
    <table>
      <thead>
        <tr>{thead}</tr>
      </thead>
      <tbody>{tbody}</tbody>
    </table>
  </body>
</html>
    """

    titles = ["id", "created_at", "workspace_name", "release_id"]
    headers = [f"<th>{title}</th>" for title in titles]
    thead = "\n".join(headers)

    row = "<tr><td>{id}</td><td>{created_at}</td><td>{workspace_name}</td><td>{release_id}</td></tr>".format(  # noqa: UP032
        id=release_file.pk,
        created_at=release_file.created_at.isoformat(),
        workspace_name=release_file.workspace.name,
        release_id=release_file.release.pk,
    )

    tbody = "\n".join(row for _ in range(100))  # add 100 rows (randomly chosen number)

    content = template.format(thead=thead, tbody=tbody)

    with release_file.absolute_path().open("w") as f:
        f.write(content)


def make_json(release_file):
    data = [
        {
            "id": release_file.pk,
            "created_at": release_file.created_at.isoformat(),
            "workspace_name": release_file.workspace.name,
            "release_id": release_file.release.pk,
        }
        for _ in range(100)  # add 100 objects (randomly chosen number)
    ]
    with release_file.absolute_path().open("w") as f:
        json.dump(data, f, indent=2)


def make_svg(release_file):
    template = """
<svg version="1.1"
     width="800" height="50"
     xmlns="http://www.w3.org/2000/svg">

  <text y="40" font-size="40" fill="black">
    ReleaseFile ID: {id}
  </text>

</svg>

    """

    content = template.format(id=release_file.id)

    with release_file.absolute_path().open("w") as f:
        f.write(content)


def make_text(release_file):
    with release_file.absolute_path().open("w") as f:
        f.write(f"Generated file for ReleaseFile ID={release_file.pk}")


class Command(BaseCommand):
    def handle(self, *args, **options):
        extension_lut = {
            ".csv": make_csv,
            ".html": make_html,
            ".json": make_json,
            ".svg": make_svg,
            ".txt": make_text,
        }

        for release_file in ReleaseFile.objects.filter(deleted_at=None):
            path = release_file.absolute_path()

            if path.exists():
                continue

            try:
                func = extension_lut[path.suffix]
            except KeyError:
                self.stderr.write(f"No template for {path.suffix}, skipping")
                continue

            # ensure the intermediate directories exist
            path.parent.mkdir(parents=True, exist_ok=True)
            func(release_file)
