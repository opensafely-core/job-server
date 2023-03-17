import textwrap

from django.conf import settings
from furl import furl


def notify_output_checkers(job_request, github_api):
    # create a ticket for output checkers
    workspace_url = furl(settings.BASE_URL) / job_request.workspace.get_absolute_url()

    body = f"""
    ### GitHub repo
    {job_request.workspace.repo.url}

    ### Workspace
    {workspace_url}

    ### Type
    - [X] I have added a label

    ### Team
    - [ ] I have added a label

    ### Details
    The outputs are located in `output/{job_request.analysis_request.pk}`
    - [ ] event_counts.csv
    - [ ] deciles_chart_counts_per_week_per_practice.png
    - [ ] top_5_code_table.csv
    - [ ] practice_count.csv
    The number of practices plotted in the deciles chart is shown in `practice_count.csv`. Check that a sufficient number of practices are included.
    The total number of events, total number of patients and the number of events within the last time period are in `event_counts.csv`. Check that these do not contain any values <=5.
    The unredacted counts underlying `top_5_code_table.csv` can be found in `counts_per_code.csv` . Check that no code with a count <=5 in `counts_per_code.csv` is included in `top_5_code_table.csv`.
    """

    return github_api.create_issue(
        org="ebmdatalab",
        repo="opensafely-output-review",
        title=f"Review request: {job_request.workspace.project.name} [{job_request.analysis_request.pk}]",
        body=textwrap.dedent(body),
        labels=["interactive"],
    )
