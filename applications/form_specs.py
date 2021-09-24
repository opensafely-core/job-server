from .form_spec_helpers import SNIPPET, Field, Fieldset, Form


form_specs = [
    Form(
        key=1,
        title="Contact details",
        sub_title="Provide the contact information for the overall application owner",
        rubric=SNIPPET,
        fieldsets=[
            Fieldset(
                label="Personal details",
                fields=[
                    Field(
                        name="full_name",
                        label="Full name",
                    ),
                    Field(
                        name="email",
                        label="Email",
                    ),
                    Field(
                        name="telephone",
                        label="Telephone number",
                    ),
                ],
            ),
            Fieldset(
                label="Organisation",
                fields=[
                    Field(
                        name="job_title",
                        label="Job title",
                    ),
                    Field(
                        name="team_name",
                        label="Team or division",
                    ),
                    Field(
                        name="organisation",
                        label="Organisation",
                    ),
                ],
            ),
        ],
    ),
    Form(
        key=2,
        title="Reasons for the request",
        sub_title="Study information",
        rubric=SNIPPET,
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
                        help_text=SNIPPET,
                    ),
                ],
            ),
        ],
    ),
    Form(
        key=3,
        title="Reasons for the request",
        sub_title="Study purpose",
        rubric=SNIPPET,
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
                    ),
                    Field(
                        name="author_email",
                        label="Work email address",
                    ),
                    Field(
                        name="author_organisation",
                        label="Affiliated organisation",
                    ),
                ],
            ),
        ],
    ),
    Form(
        key=4,
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
        key=5,
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
                    ),
                ],
            ),
        ],
    ),
    Form(
        key=6,
        title="Reasons for the request",
        sub_title="Ethical and sponsor requirements",
        rubric=SNIPPET,
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
        key=7,
        title="Reasons for the request",
        sub_title="Ethical and sponsor requirements",
        rubric=SNIPPET,
        footer=SNIPPET,
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
        key=8,
        title="Reasons for the request",
        sub_title="Ethical and sponsor requirements",
        rubric=SNIPPET,
        footer=SNIPPET,
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
                    ),
                    Field(
                        name="sponsor_email",
                        label="Sponsor email address",
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
        key=9,
        title="Reasons for the request",
        sub_title="Chief Medical Officer (CMO) priority list",
        rubric="",
        fieldsets=[
            Fieldset(
                label="CMO priority list",
                fields=[
                    Field(
                        name="is_on_cmo_priority_list",
                        label=SNIPPET,
                    ),
                ],
            ),
        ],
    ),
    Form(
        key=10,
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
                        help_text=SNIPPET,
                    ),
                ],
            ),
            Fieldset(
                label="Legal basis for record level data",
                fields=[
                    Field(
                        name="how_is_duty_of_confidentiality_satisfied",
                        label="State how you are satisfying or setting aside the common law duty of confidentiality",
                        help_text=SNIPPET,
                    ),
                ],
            ),
        ],
    ),
    Form(
        key=11,
        title="Study and team detail",
        sub_title="Study funding",
        rubric=SNIPPET,
        fieldsets=[
            Fieldset(
                label="Funding",
                fields=[
                    Field(
                        name="funding_details",
                        label="Provide details of how your research study is funded",
                    ),
                ],
            ),
        ],
    ),
    Form(
        key=12,
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
                    ),
                ],
            ),
        ],
    ),
    Form(
        key=13,
        title="Study and team detail",
        sub_title="Electronic health record (EHR) data",
        rubric=SNIPPET,
        fieldsets=[
            Fieldset(
                label="EHR data",
                fields=[
                    Field(
                        name="previous_experience_with_ehr",
                        label="Describe your previous experience of working with primary care electronic health record data (e.g. CPRD)",
                    ),
                ],
            ),
        ],
    ),
    Form(
        key=14,
        title="Study and team detail",
        sub_title="Software development coding skills",
        rubric=SNIPPET,
        fieldsets=[
            Fieldset(
                label="Script-based coding",
                fields=[
                    Field(
                        name="evidence_of_coding",
                        label="Provide evidence of you/your research group experience of using a script-based coding language",
                        help_text=SNIPPET,
                    ),
                    Field(
                        name="all_applicants_completed_getting_started",
                        label=SNIPPET,
                        help_text=SNIPPET,
                    ),
                ],
            ),
        ],
    ),
    Form(
        key=15,
        title="Study and team detail",
        sub_title="Sharing code in the public domain",
        rubric=SNIPPET,
        fieldsets=[
            Fieldset(
                label="Sharing analytic code",
                fields=[
                    Field(
                        name="evidence_of_sharing_in_public_domain_before",
                        label="Provide evidence of you/your research group sharing and documenting analytic code in the public domain",
                    ),
                ],
            ),
        ],
    ),
    Form(
        key=16,
        title="What level of OpenSAFELY platform access does each researcher require?",
        sub_title="",
        rubric="<snippet>",
        template_name="applications/page_researchers.html",
        fieldsets=[],
    ),
]
