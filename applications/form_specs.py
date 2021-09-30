from jobserver.snippets import render_snippet as snippet

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
        title="Contact details",
        sub_title="Provide the contact information for the overall application owner",
        rubric=snippet("1-rubric"),
        fieldsets=[
            Fieldset(
                label="Personal details",
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
                label="Organisation",
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
        key="study-information",
        title="Reasons for the request",
        sub_title="Study information",
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
                        help_text=snippet("2-fieldset0-field1-help_text"),
                        template_name="components/form_textarea.html",
                    ),
                ],
            ),
        ],
    ),
    Form(
        key="study-purpose",
        title="Reasons for the request",
        sub_title="Study purpose",
        rubric=snippet("3-rubric"),
        fieldsets=[
            Fieldset(
                label="Simple description",
                fields=[
                    Field(
                        name="description",
                        label="Provide a short lay description of your study purpose for the general public",
                    ),
                ],
            ),
            Fieldset(
                label="Study author",
                fields=[
                    Field(
                        name="author_name",
                        label="Name of application owner",
                        attributes=Attributes(
                            autocomplete="name",
                        ),
                    ),
                    Field(
                        name="author_email",
                        label="Work email address",
                        attributes=email_attrs,
                    ),
                    Field(
                        name="author_organisation",
                        label="Affiliated organisation",
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
        title="Reasons for the request",
        sub_title="Study data",
        rubric="",
        fieldsets=[
            Fieldset(
                label="Study data",
                fields=[
                    Field(
                        name="data_meets_purpose",
                        label="State how the data you have requested meets your purpose",
                        template_name="components/form_textarea.html",
                    ),
                    Field(
                        name="need_record_level_data",
                        label="Are you requesting record level data?",
                    ),
                ],
            ),
        ],
    ),
    Form(
        key="record-level-data",
        title="Reasons for the request",
        sub_title="Record level data",
        rubric="",
        fieldsets=[
            Fieldset(
                label="Record level data",
                fields=[
                    Field(
                        name="record_level_data_reasons",
                        label="Explain why you require access to record level data",
                        template_name="components/form_textarea.html",
                    ),
                ],
            ),
        ],
    ),
    Form(
        key="type-of-study",
        title="Reasons for the request",
        sub_title="Ethical and sponsor requirements",
        rubric=snippet("6-rubric"),
        fieldsets=[
            Fieldset(
                label="Type of study",
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
                ],
            ),
        ],
        can_continue=lambda application: (
            application.is_study_research
            or application.is_study_service_evaluation
            or application.is_study_audit
        ),
        cant_continue_message="You must select at least one purpose",
    ),
    Form(
        key="references",
        title="Reasons for the request",
        sub_title="Ethical and sponsor requirements",
        rubric=snippet("7-rubric"),
        footer=snippet("7-footer"),
        fieldsets=[
            Fieldset(
                label="HRA REC and Institutional REC",
                fields=[
                    Field(
                        name="hra_ires_id",
                        label="HRA / IRSE ID",
                    ),
                    Field(
                        name="hra_rec_reference",
                        label="HRA / REC reference",
                    ),
                    Field(
                        name="institutional_rec_reference",
                        label="Institutional REC reference",
                    ),
                ],
            ),
        ],
        prerequisite=lambda application: application.is_study_research,
    ),
    Form(
        key="sponsor-details",
        title="Reasons for the request",
        sub_title="Ethical and sponsor requirements",
        rubric=snippet("8-rubric"),
        footer=snippet("8-footer"),
        fieldsets=[
            Fieldset(
                label="Service evaluation or an audit",
                fields=[
                    Field(
                        name="institutional_rec_reference",
                        label="Institutional REC reference",
                    ),
                ],
            ),
            Fieldset(
                label="Sponsor details",
                fields=[
                    Field(
                        name="sponsor_name",
                        label="Sponsor name",
                        attributes=Attributes(
                            autocapitalize="words",
                        ),
                    ),
                    Field(
                        name="sponsor_email",
                        label="Sponsor email address",
                        attributes=email_attrs,
                    ),
                    Field(
                        name="sponsor_job_role",
                        label="Sponsor job role",
                    ),
                ],
            ),
        ],
        prerequisite=lambda application: (
            application.is_study_service_evaluation or application.is_study_audit
        ),
    ),
    Form(
        key="cmo-priority-list",
        title="Reasons for the request",
        sub_title="Chief Medical Officer (CMO) priority list",
        rubric="",
        fieldsets=[
            Fieldset(
                label=snippet("9-fieldset0-is_on_cmo_priority_list-label"),
                fields=[
                    Field(
                        name="is_on_cmo_priority_list",
                        label=snippet("9-fieldset0-field0-label"),
                    ),
                ],
            ),
        ],
    ),
    Form(
        key="legal-basis",
        title="Reasons for the request",
        sub_title="Legal basis and common law duty",
        rubric="",
        fieldsets=[
            Fieldset(
                label="Legal basis for record level data",
                fields=[
                    Field(
                        name="legal_basis_for_accessing_data_under_dpa",
                        label="State the legal basis for accessing the data under data protection law",
                        help_text=snippet("10-fieldset0-field0-help_text"),
                        template_name="components/form_textarea.html",
                    ),
                ],
            ),
            Fieldset(
                label="Legal basis for record level data",
                fields=[
                    Field(
                        name="how_is_duty_of_confidentiality_satisfied",
                        label="State how you are satisfying or setting aside the common law duty of confidentiality",
                        help_text=snippet("10-fieldset1-field0-help_text"),
                        template_name="components/form_textarea.html",
                    ),
                ],
            ),
        ],
    ),
    Form(
        key="study-funding",
        title="Study and team detail",
        sub_title="Study funding",
        rubric=snippet("11-rubric"),
        fieldsets=[
            Fieldset(
                label="Funding",
                fields=[
                    Field(
                        name="funding_details",
                        label="Provide details of how your research study is funded",
                        template_name="components/form_textarea.html",
                    ),
                ],
            ),
        ],
    ),
    Form(
        key="team-details",
        title="Study and team detail",
        sub_title="Research team",
        rubric="OpenSAFELY will need to assess the impact of onboarding your team on our own capacity.",
        fieldsets=[
            Fieldset(
                label="Team",
                fields=[
                    Field(
                        name="team_details",
                        label="Provide details of the team involved in the proposed research",
                        template_name="components/form_textarea.html",
                    ),
                ],
            ),
        ],
    ),
    Form(
        key="previous-ehr-experience",
        title="Study and team detail",
        sub_title="Electronic health record (EHR) data",
        rubric=snippet("13-rubric"),
        fieldsets=[
            Fieldset(
                label="EHR data",
                fields=[
                    Field(
                        name="previous_experience_with_ehr",
                        label="Describe your previous experience of working with primary care electronic health record data (e.g. CPRD)",
                        template_name="components/form_textarea.html",
                    ),
                ],
            ),
        ],
    ),
    Form(
        key="software-development-experience",
        title="Study and team detail",
        sub_title="Software development coding skills",
        rubric=snippet("14-rubric"),
        fieldsets=[
            Fieldset(
                label="Script-based coding",
                fields=[
                    Field(
                        name="evidence_of_coding",
                        label="Provide evidence of you/your research group experience of using a script-based coding language",
                        help_text=snippet("14-fieldset0-field0-help_text"),
                        template_name="components/form_textarea.html",
                    ),
                    Field(
                        name="all_applicants_completed_getting_started",
                        label=snippet("14-fieldset0-field1-label"),
                        help_text=snippet("14-fieldset0-field1-help_text"),
                    ),
                ],
            ),
        ],
    ),
    Form(
        key="sharing-code",
        title="Study and team detail",
        sub_title="Sharing code in the public domain",
        rubric=snippet("15-rubric"),
        fieldsets=[
            Fieldset(
                label="Sharing analytic code",
                fields=[
                    Field(
                        name="evidence_of_sharing_in_public_domain_before",
                        label="Provide evidence of you/your research group sharing and documenting analytic code in the public domain",
                        template_name="components/form_textarea.html",
                    ),
                ],
            ),
        ],
    ),
    Form(
        key="researcher-details",
        title="What level of OpenSAFELY platform access does each researcher require?",
        sub_title="",
        rubric=snippet("16-rubric"),
        template_name="applications/page_researchers.html",
        fieldsets=[],
    ),
]
