"""Functions for  specific slack messages jobserver sends.


These functions should always take a `channel` argument, so that we can test them on a different channel.
"""

from services import slack


def notify_github_release(
    path, created_by, files, backend, channel="opensafely-outputs"
):
    """
    path: path on level 4 server
    files: optional list of files released
    backend: backend released from
    """
    if files is not None:
        message = [
            f"{created_by} released {len(files)} outputs from {path} on {backend.name}:"
        ]
        for f in files:
            message.append(f"`{f}`")
    else:
        message = [f"{created_by} released outputs from {path} on {backend.name}"]

    slack.post(text="\n".join(message), channel=channel)


def notify_release_created(release, channel="opensafely-outputs"):
    workspace_url = slack.link(
        release.workspace.get_absolute_url(), release.workspace.name
    )
    release_url = slack.link(release.get_absolute_url(), "release")
    user_url = slack.link(release.created_by.get_staff_url(), release.created_by.name)

    message = f"New {release_url} requested by {user_url}. {len(release.requested_files)} files for {workspace_url} from `{release.backend.name}`"

    slack.post(message, channel)


def notify_release_file_uploaded(rfile, channel="opensafely-outputs"):
    release = rfile.release
    user = rfile.created_by

    workspace_url = slack.link(
        release.workspace.get_absolute_url(), release.workspace.name
    )
    user_url = slack.link(user.get_staff_url(), user.name)
    release_url = slack.link(release.get_absolute_url(), "release")
    file_url = slack.link(rfile.get_absolute_url(), rfile.name)

    size = round(rfile.size, 1)
    if size < 1:  # pragma: no cover
        size = "<1"

    message = f"{user_url} uploaded {file_url} ({size} Mb) to a {release_url} for {workspace_url} from `{release.backend.name}`"
    slack.post(message, channel)
