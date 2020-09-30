from django.urls import reverse

from jobserver.context_processors import nav


def test_nav_jobs(rf):
    job_list_url = reverse("job-list")
    request = rf.get(job_list_url)

    output = nav(request)

    jobs = output["nav"][1]
    workspaces = output["nav"][0]

    assert workspaces["is_active"] is False
    assert jobs["is_active"] is True


def test_nav_workspaces(rf):
    workspace_list_url = reverse("workspace-list")
    request = rf.get(workspace_list_url)

    output = nav(request)

    jobs = output["nav"][1]
    workspaces = output["nav"][0]

    assert workspaces["is_active"] is True
    assert jobs["is_active"] is False
