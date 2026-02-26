# *******************
#   IMPORTANT NOTE  *
# *******************
#
# This file lists project numbers for projects permitted to access National Data Opt-Out data.
#
# Permission must be requested from the OS service team in order to change the file
# TODO: Document the process required, when confirmed.
#
# Note also that this file is linked to in the documentation. If you move or restructure
# this file you should ensure the documentation is updated appropriately.
# https://github.com/opensafely/documentation/blob/7f8d660480fdc5e798ebe6dff6f9ed9762431736/docs/national-data-opt-outs.md

# See DPIA document for OpenSAFELY Data Analytics Service (non-COVID) linked here:
# https://digital.nhs.uk/about-nhs-digital/corporate-information-and-documents/directions-and-data-provision-notices/data-provision-notices-dpns/opensafely-data-analytics-service

# Projects operating under the OpenSAFELY COVID service are out of scope for National Data Opt-Outs
# https://digital.nhs.uk/about-nhs-digital/corporate-information-and-documents/directions-and-data-provision-notices/data-provision-notices-dpns/opensafely-covid-19-service-data-provision-notice
# Note: projects before 156 cannot be re-run, so they are not included here (several projects from 156 onwards are
# approved continuations of previous projects)
# See https://www.opensafely.org/approved-projects/ for the full list of approved projects.

# 2025-12-05: This list consists of approved projects from #156 onwards, as of 2025-12-05 (#156-200). All of these projects are COVID projects, out of scope for NDOO.
# 2026-01-13: Projects #201-205 added to the list; these projects have been confirmed as also approved under the COVID-19 Direction
# 2026-02-24: Projects #206-209 added to the list; these projects have been confirmed as also approved under the COVID-19 Direction

ANALYSIS_SCOPE_KEY = "include_ndoo"

PROJECTS_WITH_NDOO_PERMISSION = {
    # Projects identified by slug (no project number)
    "opensafely-internal",  # https://jobs.opensafely.org/opensafely-internal
    156,  # https://jobs.opensafely.org/investigating-events-following-sars-cov-2-infection-project-continuation-of-approved-project-no-12/
    157,  # https://jobs.opensafely.org/investigating-the-effectiveness-of-the-covid-19-vaccination-programme-in-the-uk-project-continuation-of-approved-project-no-22/
    158,  # https://jobs.opensafely.org/the-effect-of-covid-19-on-pancreatic-cancer-diagnosis-and-care-project-continuation-of-approved-project-no-27/
    159,  # https://jobs.opensafely.org/risk-factors-and-prediction-models-for-long-covid-project-continuation-of-approved-project-no-31/
    160,  # https://jobs.opensafely.org/coverage-effectiveness-and-safety-of-neutralising-monoclonal-antibodies-or-antivirals-for-non-hospitalised-patients-with-covid-19-project-continuation-of-approved-project-no-91/
    161,  # https://jobs.opensafely.org/covid-19-collateral-project-continuation-of-approved-project-no-95/
    162,  # https://jobs.opensafely.org/management-of-early-inflammatory-arthritis-during-the-covid-19-pandemic-project-continuation-of-approved-project-no-100/
    163,  # https://jobs.opensafely.org/explaining-the-differential-severity-of-covid-19-between-indians-in-india-and-the-uk-project-continuation-of-approved-project-no-101/
    164,  # https://jobs.opensafely.org/risk-factors-for-covid-19-disease-progression-in-immunocompromised-populations-project-continuation-of-approved-project-no-139/
    165,  # https://jobs.opensafely.org/comparison-of-risk-factors-for-hospitalizations-and-death-from-winter-infections-project-continuation-of-approved-project-no-143/
    166,  # https://jobs.opensafely.org/the-impact-of-covid-19-on-pregnancy-treatment-pathways-and-outcomes-project-continuation-of-approved-project-no-148/
    167,  # https://jobs.opensafely.org/evaluating-the-uk-shielding-policy-during-the-covid-19-pandemic-project-continuation-of-approved-project-no-150/
    168,  # https://jobs.opensafely.org/digital-access-to-primary-care-for-older-people-during-covid-project-continuation-of-approved-project-no-152/
    169,  # https://jobs.opensafely.org/long-term-kidney-outcomes-after-sars-cov-2-infection-project-continuation-of-approved-project-no-78/
    170,  # https://jobs.opensafely.org/effectiveness-of-sotrovimabmolnupiravir-use-vs-non-use-project-continuation-of-approved-project-no-115/
    171,  # https://jobs.opensafely.org/healthcare-needs-for-people-with-chronic-kidney-disease-in-the-covid-19-era-project-continuation-of-approved-project-no-137/
    172,  # https://jobs.opensafely.org/impact-and-inequalities-of-winter-pressures-in-primary-care-providing-the-evidence-base-for-mitigation-strategies/
    173,  # https://jobs.opensafely.org/analysis-of-the-pharmacy-first-element-in-the-plan-to-restore-access-to-primary-care-following-the-impact-of-covid-19/
    174,  # https://jobs.opensafely.org/echo-evaluation-of-covid-19-vaccine-histories-using-opensafely/
    175,  # https://jobs.opensafely.org/implications-of-metformin-for-long-covid/
    176,  # https://jobs.opensafely.org/comparing-disparities-in-rsv-influenza-and-covid-19/
    177,  # https://jobs.opensafely.org/effectiveness-and-safety-of-covid-19-treatments-for-hospitalised-patients/
    178,  # https://jobs.opensafely.org/long-term-complications-after-sars-cov-2-infection-in-relation-to-dialysis-and-kidney-transplantation/
    179,  # https://jobs.opensafely.org/autoimmune-diseases-following-covid-19-vaccination/
    180,  # https://jobs.opensafely.org/effects-of-the-covid-19-pandemic-upon-sodium-valproate-prescribing/
    181,  # https://jobs.opensafely.org/examining-changes-in-adhd-diagnosis-and-pathways-in-primary-care-pre-and-post-covid-pandemic/
    182,  # https://jobs.opensafely.org/incidence-of-long-term-conditions-in-england-before-and-after-the-onset-of-the-covid-19-pandemic/
    183,  # https://jobs.opensafely.org/trends-in-fluoroquinolone-use-and-reported-adverse-events-during-the-covid-19-pandemic/
    184,  # https://jobs.opensafely.org/the-incidence-of-herpes-zoster-in-people-with-immune-mediated-inflammatory-diseases-before-during-and-after-covid-19/
    185,  # https://jobs.opensafely.org/investigating-events-following-covid-19/
    186,  # https://jobs.opensafely.org/impact-of-covid-19-on-polypharmacy-and-deprescribing-patterns-in-dementia-patients/
    187,  # https://jobs.opensafely.org/describing-how-pathology-tests-and-their-associated-data-are-recorded-in-opensafely/
    188,  # https://jobs.opensafely.org/assessing-the-accuracy-and-completeness-of-death-recording-in-the-opensafely-database-compared-to-ons-death-registrations-in-england/
    189,  # https://jobs.opensafely.org/impact-of-covid-19-pandemic-on-prevalence-patterns-and-variations-of-copd-rescue-packs-prescribing-in-primary-care-in-england/
    190,  # https://jobs.opensafely.org/opensafely-feedback/
    191,  # https://jobs.opensafely.org/neurosurgery-referrals-during-the-covid-19-pandemic-can-we-determine-how-referrals-to-secondary-specialties-such-as-neurosurgery-changed-during-the-pandemic-an-exploratory-study/
    192,  # https://jobs.opensafely.org/exercise-pegasus-red-team-validation/
    193,  # https://jobs.opensafely.org/incidence-and-management-of-inflammatory-rheumatic-diseases-before-during-and-after-the-covid-19-pandemic/
    194,  # https://jobs.opensafely.org/short-data-report-recording-of-personalised-follow-up-pathways-in-opensafely/
    195,  # https://jobs.opensafely.org/effect-of-statin-use-on-the-incidence-of-severe-covid-19/
    196,  # https://jobs.opensafely.org/openpregnosis-developing-an-open-algorithm-to-identify-pregnancy-episodes-and-outcomes-in-opensafely/
    197,  # https://jobs.opensafely.org/neurosurgery-referrals-during-the-covid-19-pandemic-a-retrospective-cohort-study-using-opensafely/
    198,  # https://jobs.opensafely.org/identify-risk-factors-associated-with-disparities-for-resistant-bloodstream-infections-before-during-and-after-the-global-covid-19-pandemic-a-national-case-control-and-cohort-study/
    199,  # https://jobs.opensafely.org/effects-of-the-covid-19-pandemic-on-antibiotic-prescribing/
    200,  # https://jobs.opensafely.org/burden-of-neurodegenerative-disease-2020-2024/
    201,  # https://jobs.opensafely.org/impact-of-covid-19-pandemic-on-life-expectancy-among-people-with-hiv/
    202,  # https://jobs.opensafely.org/a-longitudinal-evaluation-of-pharmacy-consultation-services-including-the-pharmacy-first-programme-on-healthcare-utilisation-over-the-period-2017-2026/
    203,  # https://jobs.opensafely.org/migration-related-coding-in-english-primary-care-electronic-health-records/
    204,  # https://jobs.opensafely.org/the-effect-of-the-covid-19-pandemic-on-ae-attendances-for-cardiovascular-diseases/
    205,  # https://jobs.opensafely.org/short-data-report-recording-of-medicines-prescribed-outside-primary-care-in-gp-ehr-data/
    206,  # https://jobs.opensafely.org/cardiovascular-outcomes-post-covid-19-and-the-potential-for-covid-19-vaccines-to-mitigate-them/
    207,  # https://jobs.opensafely.org/recording-of-additional-prescription-information-in-opensafely/
    208,  #    https://jobs.opensafely.org/diagnostics-demand-optimisation/
    209,  # https://jobs.opensafely.org/sars-covid-19-vaccination-and-risk-of-major-adverse-cardiac-events-after-hip-fracture/
}


def project_has_permission(project):
    if not project.number:
        return project.slug in PROJECTS_WITH_NDOO_PERMISSION
    return project.number in PROJECTS_WITH_NDOO_PERMISSION


def analysis_scope_for_project(project):
    if project_has_permission(project):
        return ANALYSIS_SCOPE_KEY
