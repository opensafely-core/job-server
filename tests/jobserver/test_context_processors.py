from django.urls import reverse

from jobserver.context_processors import nav


def test_nav_jobs(rf):
    job_list_url = reverse("job-list")
    request = rf.get(job_list_url)

    output = nav(request)

    jobs = output["nav"][0]
    status = output["nav"][1]

    assert jobs["is_active"] is True
    assert status["is_active"] is False
