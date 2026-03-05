# *******************
#   IMPORTANT NOTE  *
# *******************
#
# This file lists project numbers for projects permitted to access restricted (non-core) datasets.
#
# Permission must be requested from the OS service team in order to change the file
# TODO: Document the process required, when confirmed.
#
# Note also that this file is linked to in the documentation. If you move or restructure
# this file you should ensure the documentation is updated appropriately.
# https://github.com/opensafely/documentation/blob/b070dd45d109314fa1bf119237937b9cadfc79df/docs/data-sources/index.md
#
# Historically (prior to Non-COVID opening), most table permissions were governed by IG, and can be found in the project spreadsheet:
# https://docs.google.com/spreadsheets/d/1odgWEwFrkmCr3-7leE2amwVA3b55UCOzbXQOiNgyb1w/edit
#
# However, appointments and wl_* (waiting_list) table permissions are restricted for non_IG reasons, in that
# their data need handling with due attention. Appointments is access managed by Alex, and
# waiting_list table access is TBC.


PROJECTS_WITH_PERMISSION = {
    # Projects identified by slug (no project number)
    # OpenSAFELY Internal project for curation: https://jobs.opensafely.org/opensafely-internal
    "opensafely-internal": ["icnarc", "appointments"],
    # https://jobs.opensafely.org/impact-of-covid-19-on-long-term-healthcare-use-and-costs-in-children-and-young-people/
    "9": ["isaric"],
    # https://jobs.opensafely.org/deaths-at-home-during-covid-19/
    "34": ["appointments"],
    # https://jobs.opensafely.org/long-term-kidney-outcomes-after-sars-cov-2-infection/
    "78": ["appointments"],
    # https://jobs.opensafely.org/validation-of-the-opensafely-kidney-codes/
    "87": ["ukrr"],
    # https://jobs.opensafely.org/effectiveness-safety-sotrovimab-molnupiravir/
    "106": ["ukrr"],
    # https://jobs.opensafely.org/covid-19-vaccine-coverage-and-effectiveness-in-chronic-kidney-disease-patients/
    "110": ["ukrr"],
    # https://jobs.opensafely.org/opioid-prescribing-trends-and-changes-during-covid-19/
    "122": ["waiting_list"],
    # https://jobs.opensafely.org/curation-of-gp-appointments-data-short-data-report/
    "129": ["appointments"],
    # https://jobs.opensafely.org/gp-appointments-during-covid/
    "136": ["appointments"],
    # https://jobs.opensafely.org/digital-access-to-primary-care-for-older-people-during-covid/
    "152": ["appointments"],
    # https://jobs.opensafely.org/validation-of-isaric-sus-phosp-data-for-covid-related-hospital-admissions/
    "154": ["isaric"],
    # https://jobs.opensafely.org/the-effect-of-long-covid-on-quality-adjusted-life-years-using-openprompt/
    "155": ["open_prompt"],
    # https://jobs.opensafely.org/investigating-events-following-sars-cov-2-infection-project-continuation-of-approved-project-no-12/
    "156": ["appointments"],
    # https://jobs.opensafely.org/the-impact-of-covid-19-on-pregnancy-treatment-pathways-and-outcomes-project-continuation-of-approved-project-no-148/
    "166": ["appointments"],
    # https://jobs.opensafely.org/healthcare-needs-for-people-with-chronic-kidney-disease-in-the-covid-19-era-project-continuation-of-approved-project-no-137/
    "171": ["appointments", "ukrr"],
    # https://jobs.opensafely.org/impact-and-inequalities-of-winter-pressures-in-primary-care-providing-the-evidence-base-for-mitigation-strategies/
    "172": [
        "appointments",
        "sgss_covid_all_tests",
        "occupation_on_covid_vaccine_record",
    ],
    # https://jobs.opensafely.org/implications-of-metformin-for-long-covid/
    "175": [
        "appointments",
        "sgss_covid_all_tests",
        "occupation_on_covid_vaccine_record",
    ],
    # https://jobs.opensafely.org/effectiveness-and-safety-of-covid-19-treatments-for-hospitalised-patients/
    "177": ["covid_therapeutics", "sgss_covid_all_tests"],
    # https://jobs.opensafely.org/investigating-events-following-covid-19/
    "185": [
        "appointments",
        "sgss_covid_all_tests",
        "occupation_on_covid_vaccine_record",
    ],
    # https://jobs.opensafely.org/identify-risk-factors-associated-with-disparities-for-resistant-bloodstream-infections-before-during-and-after-the-global-covid-19-pandemic-a-national-case-control-and-cohort-study/
    "198": ["sgss_covid_all_tests"],
    # https://jobs.opensafely.org/sars-covid-19-vaccination-and-risk-of-major-adverse-cardiac-events-after-hip-fracture/
    "209": ["sgss_covid_all_tests"],
}


def analysis_scope_for_project(project):
    if not project.number:
        return PROJECTS_WITH_PERMISSION.get(project.slug, [])
    return PROJECTS_WITH_PERMISSION.get(project.number, [])
