import textwrap

from django.conf import settings
from furl import furl


def notify_output_checkers(job_request, github_api):
    workspace_url = furl(settings.BASE_URL) / job_request.workspace.get_absolute_url()

    body = f"""
    ### GitHub repo
    {job_request.workspace.repo.url}

    ### Workspace
    {workspace_url}

    ### Analysis request purpose
    {job_request.analysis_request.purpose}

    ### Details
    The outputs are located in `output/{job_request.analysis_request.pk}`
    - [ ] `output/{job_request.analysis_request.pk}/report.html`

    The report shows:
    - Summary table with the total number of events and the number of unique patients experiencing these events as well as the number of events in the latest period and latest week. These are rounded to the nearest 100.
    - Practice level deciles chart. The number of practices included is shown in the report.
    - Tables of the top 5 most common codes for both codelists. This is calculated as the proportion of each code across all codes recorded in the study period. A version of these tables with the counts for each code can be found in `output/{job_request.analysis_request.pk}/joined/top_5_code_table_with_counts_1.csv`  and `output/{job_request.analysis_request.pk}/joined/top_5_code_table_with_counts_2.csv`. Codes with counts <=7 are removed. Counts rounded to the nearest 7 before the proportion is calculated.
    - Population level rate per 1000 for the measure. Counts are rounded to the nearest 10 before calculating the rate. The underlying data can be found in `output/{job_request.analysis_request.pk}/joined/measure_total_rate.csv`.
    - Population level rate per 1000 for the measure, broken down demographics. Counts are rounded to the nearest 10 before calculating the rate. The underlying data can be found in `output/{job_request.analysis_request.pk}/joined/measure_*_rate.csv`.

    ### Releasing
    To release the outputs, go into the **root** of the workspace and run:

    ```
    osrelease output/{job_request.analysis_request.pk}/report.html
    ```
    The HTML report contains all relevant data, so the individual CSVs and images do NOT need to be released.
    """

    return github_api.create_issue(
        org="ebmdatalab",
        repo="opensafely-output-review",
        title=f"Review request: {job_request.workspace.project.name} [{job_request.analysis_request.pk}]",
        body=textwrap.dedent(body),
        labels=["interactive"],
    )
