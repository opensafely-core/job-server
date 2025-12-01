# *******************
#   IMPORTANT NOTE  *
# *******************
#
# This file lists project numbers for projects permitted to access National Data Opt-Out data.
#
# Permission must be requested from the OS service team in order to change the file
# TODO: Document the process required, when confirmed.
#
# TODO: When this file is linked to in the docs, add a similar comment to the one in t1oo.py

# See DPIA document for OpenSAFELY Data Analytics Service (non-COVID) linked here:
# https://digital.nhs.uk/about-nhs-digital/corporate-information-and-documents/directions-and-data-provision-notices/data-provision-notices-dpns/opensafely-data-analytics-service

# Projects operating under the OpenSAFELY COVID service are out of scope for National Data Opt-Outs
# https://digital.nhs.uk/about-nhs-digital/corporate-information-and-documents/directions-and-data-provision-notices/data-provision-notices-dpns/opensafely-covid-19-service-data-provision-notice
# TODO: Complete this list! Currently just includes a few of projects for example purposes
# Note: projects before 156 cannot be re-run, so they are not included here (several projects from 156 onwards are
# approved continuations of previous projects)
ANALYSIS_SCOPE_KEY = "include_ndoo"

PROJECTS_WITH_NDOO_PERMISSION = {
    156,  # https://jobs.opensafely.org/investigating-events-following-sars-cov-2-infection-project-continuation-of-approved-project-no-12/
    157,  # https://jobs.opensafely.org/investigating-the-effectiveness-of-the-covid-19-vaccination-programme-in-the-uk-project-continuation-of-approved-project-no-22/
    158,  # https://jobs.opensafely.org/the-effect-of-covid-19-on-pancreatic-cancer-diagnosis-and-care-project-continuation-of-approved-project-no-27/
    159,  # https://jobs.opensafely.org/risk-factors-and-prediction-models-for-long-covid-project-continuation-of-approved-project-no-31/
}


def project_has_permission(project):
    if not project.number:
        return False
    return project.number in PROJECTS_WITH_NDOO_PERMISSION


def analysis_scope_for_project(project):
    if project_has_permission(project):
        return ANALYSIS_SCOPE_KEY
