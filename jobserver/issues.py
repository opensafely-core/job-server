from django.conf import settings
from furl import furl

from .utils import strip_whitespace


def _size_formatter(value):
    """
    Format the value, in bytes, with a size suffix

    Kilobytes (Kb) and Megabytes (Mb) will be automatically selected if the
    values is large enough.
    """
    if value < 1024:
        return f"{value}b"

    if value < 1024**2:
        value = round(value / 1024, 2)
        return f"{value}Kb"

    value = round(value / 1024**2, 2)
    return f"{value}Mb"


def create_copilot_publish_report_request(report, github_api):
    copilot_name = report.project.copilot
    if not copilot_name:
        copilot_name = ""

    base_url = furl(settings.BASE_URL)
    project_url = base_url / report.project.get_staff_url()
    report_url = base_url / report.get_absolute_url()
    report_staff_url = base_url / report.get_staff_url()

    body = f"""
    ### Report details
    Copilot: {copilot_name}
    Project: {project_url}
    Report: {report_url}

    ### Checklist

    1. Co-pilot carries out assurance checks[^1]
        - [ ] Assurance check (co-pilot)
          - [ ] Do the results of the project match the original aims of the application?
          - [ ] Are the results COPI compliant?
          - [ ] Are the analysis and discussion focused on a COVID-19 related theme?
          - [ ] Have non COVID-19 related inferences been made, and how extensive are they?
          - [ ] Are all assumptions about the study population/data appropriate and reasonable?
          - [ ] Have the authors interpreted the results appropriately? (There is a risk that these users will not be sufficiently experienced to judge if the quality of the GP data will be good enough to answer their questions. We have agreed to mitigate this risk by checking their reports carefully before publication.)
          - [ ] Are all necessary limitations included?
          - [ ] Are all recommendations appropriate and reasonable?
          - [ ] Is there any contentious or politically sensitive content?
          - [ ] Are NHSE or any other organisations likely to want the right to reply?
    2. If required[^2], co-pilot shares the manuscript with Ops Team[^3] and Amir.
        - [ ] Ops Team review (Ops Team member)
        - [ ] IG review (@amirmehrkar)
        - [ ] Co-pilot corresponds with pilot regarding changes. To make a change, the co-pilot must reject the current request and ask the user to make edits and then re-submit the request.

    ** Steps 2-4 are repeated as required to meet assurance checks **

    3. Co-pilot downloads a copy of the report and submits to Amir, who will prompt IG review with NHSE
        - [ ] Report submitted to Amir for NHSE review
    4. Amir informs co-pilot of decision (accept/reject)
    5. Co-pilot approves or rejects the request [on the report page]({report_staff_url})
    6. Upon publication, co-pilot should consider if project status10 should be updated, and if any external outputs should be linked to in the status description
        - [ ] Project status updated


    [^1]: Further details regarding what is included in an assurance check is available [here](https://bennettinstitute-team-manual.pages.dev/products/publication-process-copiloted/#assurance-check).
    [^2]: If the assurance check raises any issues.
    [^3]: Further information about the Ops Team is available [here](https://bennettinstitute-team-manual.pages.dev/the-teams/ops-team/).
    """

    body = strip_whitespace(body)

    data = github_api.create_issue(
        org="ebmdatalab",
        repo="publications-copiloted",
        title=f"OSI Report: {report.title}",
        body=body,
        labels=["publication-copiloted"],
    )

    return data["html_url"]


def create_output_checking_request(release, github_api):
    is_internal = release.created_by.orgs.filter(slug="datalab").exists()

    files = release.files.all()
    number = len(files)
    size = _size_formatter(sum(f.size for f in files))
    review_form = "" if is_internal else "[Review request form]()"

    base_url = furl(settings.BASE_URL)
    release_url = base_url / release.get_absolute_url()
    requester_url = base_url / release.created_by.get_staff_url()
    workspace_url = base_url / release.workspace.get_absolute_url()

    body = f"""
    Requested by: [{release.created_by.name}]({requester_url})
    Release: [{release.id}]({release_url})
    GitHub repo: [{release.workspace.repo.name}]({release.workspace.repo.url})
    Workspace: [{release.workspace.name}]({workspace_url})

    {number} files have been selected for review, with a total size of {size}.

    {review_form}

    **When you start a review please react to this message with :eyes:. When you have completed your review add a :thumbsup:. Once two reviews have been completed and a response has been sent to the requester, please close the issue.**
    """

    body = strip_whitespace(body)

    data = github_api.create_issue(
        org="ebmdatalab",
        repo="opensafely-output-review",
        title=release.workspace.name,
        body=body,
        labels=["internal" if is_internal else "external"],
    )

    return data["html_url"]


def create_switch_repo_to_public_request(repo, user, github_api):
    body = f"""
    The [{repo.name}]({repo.url}) repo is ready to be made public.

    This repo has been checked and approved by {user.name}.

    An owner of the `opensafely` org is required to make this change, they can do so on the [repo settings page]({repo.url}/settings).

    Once the repo is public please close this issue.
    """

    body = strip_whitespace(body)

    data = github_api.create_issue(
        org="ebmdatalab",
        repo="tech-support",
        title=f"Switch {repo.name} repo to public",
        body=body,
        labels=[],
    )

    return data["html_url"]
