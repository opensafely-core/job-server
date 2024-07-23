from jobserver.snippets import render_snippet as snippet

from . import models
from .form_spec_helpers import Attributes, Field, Fieldset, Form


email_attrs = Attributes(
    type="email",
    inputmode="email",
    autocomplete="email",
    autocapitalize="off",
    spellcheck="false",
    autocorrect="off",
)

form_specs = [
    Form(
        key="contact-details",
        model=models.ContactDetailsPage,
        title="Contact details",
        sub_title="Provide the contact information for the key contact for overall application",
        rubric=snippet("1-rubric"),
        fieldsets=[
            Fieldset(
                label="Key contact details",
                fields=[
                    Field(
                        name="full_name",
                        label="Full name",
                        attributes=Attributes(
                            autocomplete="name",
                            autocapitalize="words",
                        ),
                    ),
                    Field(
                        name="email",
                        label="Email",
                        attributes=email_attrs,
                    ),
                    Field(
                        name="telephone",
                        label="Telephone number",
                        attributes=Attributes(
                            type="tel",
                            inputmode="tel",
                            autocomplete="tel",
                        ),
                    ),
                ],
            ),
            Fieldset(
                label="Key contact organisation",
                fields=[
                    Field(
                        name="job_title",
                        label="Job title",
                        attributes=Attributes(
                            autocomplete="organization-title",
                        ),
                    ),
                    Field(
                        name="team_name",
                        label="Team or division",
                    ),
                    Field(
                        name="organisation",
                        label="Organisation",
                        attributes=Attributes(
                            autocomplete="organization",
                        ),
                    ),
                ],
            ),
        ],
    ),
    Form(
        key="commercial-involvement",
        model=models.CommercialInvolvementPage,
        title="Commercial Involvement",
        sub_title="",
        rubric=snippet("commercial-involvement-rubric"),
        fieldsets=[
            Fieldset(
                label="",
                fields=[
                    Field(
                        name="details",
                        label="Details",
                        template_name="form_textarea",
                    ),
                ],
            ),
        ],
    ),
    Form(
        key="study-information",
        model=models.StudyInformationPage,
        title="Study information",
        sub_title="Reason for the request",
        rubric=snippet("2-rubric"),
        fieldsets=[
            Fieldset(
                label="Study information",
                fields=[
                    Field(
                        name="study_name",
                        label="Study name",
                        help_text="This should be a short public-friendly name.",
                    ),
                    Field(
                        name="study_purpose",
                        label="What is the purpose for which you are requesting access to the OpenSAFELY data?",
                        help_text=snippet("study_purpose-help_text"),
                        template_name="form_textarea",
                    ),
                    Field(
                        name="read_analytic_methods_policy",
                        label="Have all applicants for OpenSAFELY read and agreed to the OpenSAFELY Analytic Methods Policy?",
                        help_text=snippet("read_analytic_methods_policy-help_text"),
                    ),
                ],
            ),
        ],
    ),
    Form(
        key="study-purpose",
        model=models.StudyPurposePage,
        title="Study purpose",
        sub_title="",
        rubric=snippet("3-rubric"),
        fieldsets=[
            Fieldset(
                label="Simple description",
                fields=[
                    Field(
                        name="description",
                        label="Provide a short lay description of your study purpose for the general public",
                        help_text=snippet("description-help_text"),
                        template_name="form_textarea",
                        attributes=Attributes(maxlength=2500),
                    ),
                ],
            ),
            Fieldset(
                label="Topic areas",
                fields=[
                    Field(
                        name="is_covid_prevention",
                        label="COVID transmission/prevalence/non-pharmaceutical prevention",
                    ),
                    Field(
                        name="is_risk_from_covid",
                        label="Risk from COVID (short term) [e.g. hospitalisation/death]",
                    ),
                    Field(
                        name="is_post_covid_health_impacts",
                        label="Post-COVID health impacts [e.g. long COVID]",
                    ),
                    Field(
                        name="is_covid_vaccine_eligibility_or_coverage",
                        label="COVID vaccine eligibility/coverage",
                    ),
                    Field(
                        name="is_covid_vaccine_effectiveness_or_safety",
                        label="COVID vaccine effectiveness/safety",
                    ),
                    Field(
                        name="is_other_impacts_of_covid",
                        label="Other/indirect impacts of COVID on health/healthcare",
                    ),
                ],
            ),
            Fieldset(
                label="Study lead(s)",
                fields=[
                    Field(
                        name="author_name",
                        label="Name(s)",
                        attributes=Attributes(
                            autocomplete="name",
                        ),
                    ),
                    Field(
                        name="author_email",
                        label="Email(s)",
                    ),
                    Field(
                        name="author_organisation",
                        label="Organisation(s)",
                        attributes=Attributes(
                            autocomplete="organization",
                        ),
                    ),
                ],
            ),
        ],
    ),
    Form(
        key="study-data",
        model=models.StudyDataPage,
        title="Study data",
        sub_title="",
        rubric="",
        fieldsets=[
            Fieldset(
                label="",
                fields=[
                    Field(
                        name="need_record_level_data",
                        label="Does your study need access to patient level data?",
                    ),
                ],
            ),
            Fieldset(
                label="",
                fields=[
                    Field(
                        name="data_meets_purpose",
                        label="If NO, please explain why using OpenSAFELY is necessary to answer your study question(s)",
                        help_text=snippet("patient-level"),
                        template_name="form_textarea",
                        optional=True,
                    ),
                ],
            ),
        ],
    ),
    Form(
        key="datasets",
        model=models.DatasetsPage,
        title="Datasets",
        sub_title="",
        rubric=snippet("datasets-rubric"),
        fieldsets=[
            Fieldset(
                label="Please confirm if you need to access any of the following datasets",
                fields=[
                    Field(
                        name="needs_icnarc",
                        label="ICNARC",
                    ),
                    Field(
                        name="needs_isaric",
                        label="ISARIC",
                    ),
                    Field(
                        name="needs_ons_cis",
                        label="ONS-CIS (community infection survey)",
                    ),
                    Field(name="needs_phosp", label="PHOSP"),
                    Field(name="needs_ukrr", label="UK Renal Registry (UKRR)"),
                ],
            ),
        ],
    ),
    Form(
        key="record-level-data",
        model=models.RecordLevelDataPage,
        title="Backend data environment (TPP and EMIS)",
        sub_title="",
        rubric="",
        fieldsets=[
            Fieldset(
                label="",
                fields=[
                    Field(
                        name="record_level_data_reasons",
                        label="If requesting OpenSAFELY-EMIS access please specify the justification",
                        help_text=snippet("emis_justification"),
                        template_name="form_textarea",
                    ),
                ],
            ),
        ],
    ),
    Form(
        key="type-of-study",
        model=models.TypeOfStudyPage,
        title="Type of study",
        sub_title="",
        rubric=snippet("6-rubric"),
        fieldsets=[
            Fieldset(
                label="What type of study are you performing?",
                fields=[
                    Field(
                        name="is_study_research",
                        label="Research",
                    ),
                    Field(
                        name="is_study_service_evaluation",
                        label="Service evaluation",
                    ),
                    Field(
                        name="is_study_audit",
                        label="Audit",
                    ),
                    Field(
                        name="is_study_short_data_report",
                        label="Short data report (Data Curation Project)",
                    ),
                ],
            ),
        ],
        can_continue=lambda application: (
            application.is_study_research
            or application.is_study_service_evaluation
            or application.is_study_audit
            or application.is_study_short_data_report
        ),
        cant_continue_message="You must select at least one purpose",
    ),
    Form(
        key="references",
        model=models.ReferencesPage,
        title="Research references",
        sub_title="",
        rubric=snippet("references-rubric"),
        footer=snippet("references-footer"),
        fieldsets=[
            Fieldset(
                label="HRA REC and Institutional REC",
                fields=[
                    Field(
                        name="hra_ires_id",
                        label="HRA / IRAS ID",
                    ),
                    Field(
                        name="hra_rec_reference",
                        label="HRA / REC reference",
                    ),
                    Field(
                        name="institutional_rec_reference",
                        label="If using ONS-CIS, ONS ethics approval reference",
                        optional=True,
                    ),
                ],
            ),
        ],
        prerequisite=lambda application: application.is_study_research,
    ),
    Form(
        key="service-evaluation-audit",
        model=models.SponsorDetailsPage,
        title="Service evaluation or audit",
        sub_title="",
        rubric=snippet("service-evaluation-audit-rubric"),
        footer=snippet("service-evaluation-audit-footer"),
        fieldsets=[
            Fieldset(
                label="",
                fields=[
                    Field(
                        name="is_member_of_bennett_or_lshtm",
                        label="I am a member of the Bennett Institute/LSHTM conducting a study conforming to the Service Restoration Observatory and Aftershocks workstream",
                    )
                ],
            ),
            Fieldset(
                label="",
                fields=[
                    Field(
                        name="institutional_rec_reference",
                        label="Institutional REC reference",
                        optional=True,
                    ),
                ],
            ),
            Fieldset(
                label="Sponsor information",
                fields=[
                    Field(
                        name="sponsor_name",
                        label="Sponsor name",
                        attributes=Attributes(
                            autocapitalize="words",
                        ),
                        optional=True,
                    ),
                    Field(
                        name="sponsor_email",
                        label="Sponsor email address",
                        attributes=email_attrs,
                        optional=True,
                    ),
                    Field(
                        name="sponsor_job_role",
                        label="Sponsor job role",
                        optional=True,
                    ),
                ],
            ),
        ],
        prerequisite=lambda application: (
            application.is_study_service_evaluation or application.is_study_audit
        ),
    ),
    Form(
        key="short-data-report",
        model=models.ShortDataReportPage,
        title="Short Data Report",
        sub_title="",
        rubric=snippet("short-data-report-rubric"),
        fieldsets=[],
        prerequisite=lambda application: application.is_study_short_data_report,
    ),
    Form(
        key="study-funding",
        model=models.StudyFundingPage,
        title="Study funding",
        sub_title="",
        rubric=snippet("11-rubric"),
        fieldsets=[
            Fieldset(
                label="Funding",
                fields=[
                    Field(
                        name="funding_details",
                        label="Provide details of how your research study is funded",
                        template_name="form_textarea",
                    ),
                ],
            ),
        ],
    ),
    Form(
        key="team-details",
        model=models.TeamDetailsPage,
        title="Research team",
        sub_title="",
        rubric="OpenSAFELY will need to assess the impact of onboarding your team on our own capacity.",
        fieldsets=[
            Fieldset(
                label="Team details",
                fields=[
                    Field(
                        name="team_details",
                        label="Provide details of the team involved in the proposed research",
                        template_name="form_textarea",
                    ),
                ],
            ),
        ],
    ),
    Form(
        key="previous-ehr-experience",
        model=models.PreviousEhrExperiencePage,
        title="Electronic health record (EHR) data",
        sub_title="",
        rubric=snippet("13-rubric"),
        fieldsets=[
            Fieldset(
                label="EHR data",
                fields=[
                    Field(
                        name="previous_experience_with_ehr",
                        label="Describe your previous experience of working with primary care electronic health record data",
                        template_name="form_textarea",
                        help_text=snippet("previous_experience_with_ehr_help_text"),
                    ),
                ],
            ),
        ],
    ),
    Form(
        key="software-development-experience",
        model=models.SoftwareDevelopmentExperiencePage,
        title="Software development experience",
        sub_title="",
        rubric=snippet("14-rubric"),
        fieldsets=[
            Fieldset(
                label="Script-based coding",
                fields=[
                    Field(
                        name="evidence_of_coding",
                        label="Provide evidence of you/your research group experience of using a script-based coding language",
                        help_text=snippet("14-fieldset0-field0-help_text"),
                        template_name="form_textarea",
                    ),
                ],
            ),
            Fieldset(
                label="",
                fields=[
                    Field(
                        name="all_applicants_completed_getting_started",
                        label="Have all applicants for OpenSAFELY access completed the Getting Started tutorial?",
                        help_text=snippet("14-fieldset0-field1-help_text"),
                    ),
                ],
            ),
        ],
    ),
    Form(
        key="sharing-code",
        model=models.SharingCodePage,
        title="Sharing code in the public domain",
        sub_title="",
        rubric=snippet("15-rubric"),
        fieldsets=[
            Fieldset(
                label="Sharing analytic code",
                fields=[
                    Field(
                        name="evidence_of_sharing_in_public_domain_before",
                        label="Provide evidence of you/your research group sharing and documenting analytic code in the public domain",
                        template_name="form_textarea",
                    ),
                ],
            ),
        ],
    ),
    Form(
        key="researcher-details",
        model=models.ResearcherDetailsPage,
        title="Researchers",
        sub_title="What level of OpenSAFELY platform access does each researcher require?",
        rubric=snippet("16-rubric"),
        template_name="applications/page_researchers.html",
        fieldsets=[],
    ),
]
