SNIPPET = "<snippet>"


def form(
    *,
    key,
    title,
    sub_title,
    fieldsets,
    rubric,
    footer="",
    can_continue=None,
    cant_continue_message=None,
    prerequisite=None,
):
    return {
        "key": key,
        "title": title,
        "sub_title": sub_title,
        "rubric": rubric,
        "footer": footer,
        "fieldsets": fieldsets,
        "can_continue": can_continue or (lambda application: True),
        "cant_continue_message": cant_continue_message,
        "prerequisite": prerequisite or (lambda application: True),
    }


def fieldset(*, label, fields):
    return {
        "label": label,
        "fields": fields,
    }


def field(*, name, label, help_text=""):
    return {
        "name": name,
        "label": label,
        "help_text": help_text,
    }


form_specs = [
    form(
        key=1,
        title="Contact details",
        sub_title="Provide the contact information for the overall application owner",
        rubric=SNIPPET,
        fieldsets=[
            fieldset(
                label="Personal details",
                fields=[
                    field(
                        name="full_name",
                        label="Full name",
                    ),
                    field(
                        name="email",
                        label="Email",
                    ),
                    field(
                        name="telephone",
                        label="Telephone number",
                    ),
                ],
            ),
            fieldset(
                label="Organisation",
                fields=[
                    field(
                        name="job_title",
                        label="Job title",
                    ),
                    field(
                        name="team_name",
                        label="Team or division",
                    ),
                    field(
                        name="organisation",
                        label="Organisation",
                    ),
                ],
            ),
        ],
    ),
    form(
        key=2,
        title="Reasons for the request",
        sub_title="Study information",
        rubric=SNIPPET,
        fieldsets=[
            fieldset(
                label="Study information",
                fields=[
                    field(
                        name="study_name",
                        label="Study name",
                        help_text="This should be a short public-friendly name.",
                    ),
                    field(
                        name="study_purpose",
                        label="What is the purpose for which you are requesting access to the OpenSAFELY data?",
                        help_text=SNIPPET,
                    ),
                ],
            ),
        ],
    ),
    form(
        key=3,
        title="Reasons for the request",
        sub_title="Study purpose",
        rubric=SNIPPET,
        fieldsets=[
            fieldset(
                label="Simple description",
                fields=[
                    field(
                        name="description",
                        label="Provide a short lay description of your study purpose for the general public",
                    ),
                ],
            ),
            fieldset(
                label="Study author",
                fields=[
                    field(
                        name="author_name",
                        label="Name of application owner",
                    ),
                    field(
                        name="author_email",
                        label="Work email address",
                    ),
                    field(
                        name="author_organisation",
                        label="Affiliated organisation",
                    ),
                ],
            ),
        ],
    ),
    form(
        key=4,
        title="Reasons for the request",
        sub_title="Study data",
        rubric="",
        fieldsets=[
            fieldset(
                label="Study data",
                fields=[
                    field(
                        name="data_meets_purpose",
                        label="State how the data you have requested meets your purpose",
                    ),
                    field(
                        name="need_record_level_data",
                        label="Are you requesting record level data?",
                    ),
                ],
            ),
        ],
    ),
    form(
        key=5,
        title="Reasons for the request",
        sub_title="Record level data",
        rubric="",
        fieldsets=[
            fieldset(
                label="Record level data",
                fields=[
                    field(
                        name="record_level_data_reasons",
                        label="Explain why you require access to record level data",
                    ),
                ],
            ),
        ],
    ),
    form(
        key=6,
        title="Reasons for the request",
        sub_title="Ethical and sponsor requirements",
        rubric=SNIPPET,
        fieldsets=[
            fieldset(
                label="Type of study",
                fields=[
                    field(
                        name="is_study_research",
                        label="Research",
                    ),
                    field(
                        name="is_study_service_evaluation",
                        label="Service evaluation",
                    ),
                    field(
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
    form(
        key=7,
        title="Reasons for the request",
        sub_title="Ethical and sponsor requirements",
        rubric=SNIPPET,
        footer=SNIPPET,
        fieldsets=[
            fieldset(
                label="HRA REC and Institutional REC",
                fields=[
                    field(
                        name="hra_ires_id",
                        label="HRA / IRSE ID",
                    ),
                    field(
                        name="hra_rec_reference",
                        label="HRA / REC reference",
                    ),
                    field(
                        name="institutional_rec_reference",
                        label="Institutional REC reference",
                    ),
                ],
            ),
        ],
        prerequisite=lambda application: application.is_study_research,
    ),
    form(
        key=8,
        title="Reasons for the request",
        sub_title="Ethical and sponsor requirements",
        rubric=SNIPPET,
        footer=SNIPPET,
        fieldsets=[
            fieldset(
                label="Service evaluation or an audit",
                fields=[
                    field(
                        name="institutional_rec_reference",
                        label="Institutional REC reference",
                    ),
                ],
            ),
            fieldset(
                label="Sponsor details",
                fields=[
                    field(
                        name="sponsor_name",
                        label="Sponsor name",
                    ),
                    field(
                        name="sponsor_email",
                        label="Sponsor email address",
                    ),
                    field(
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
    form(
        key=9,
        title="Reasons for the request",
        sub_title="Chief Medical Officer (CMO) priority list",
        rubric="",
        fieldsets=[
            fieldset(
                label="CMO priority list",
                fields=[
                    field(
                        name="is_on_cmo_priority_list",
                        label=SNIPPET,
                    ),
                ],
            ),
        ],
    ),
    form(
        key=10,
        title="Reasons for the request",
        sub_title="Legal basis and common law duty",
        rubric="",
        fieldsets=[
            fieldset(
                label="Legal basis for record level data",
                fields=[
                    field(
                        name="legal_basis_for_accessing_data_under_dpa",
                        label="State the legal basis for accessing the data under data protection law",
                        help_text=SNIPPET,
                    ),
                ],
            ),
            fieldset(
                label="Legal basis for record level data",
                fields=[
                    field(
                        name="how_is_duty_of_confidentiality_satisfied",
                        label="State how you are satisfying or setting aside the common law duty of confidentiality",
                        help_text=SNIPPET,
                    ),
                ],
            ),
        ],
    ),
    form(
        key=11,
        title="Study and team detail",
        sub_title="Study funding",
        rubric=SNIPPET,
        fieldsets=[
            fieldset(
                label="Funding",
                fields=[
                    field(
                        name="funding_details",
                        label="Provide details of how your research study is funded",
                    ),
                ],
            ),
        ],
    ),
    form(
        key=12,
        title="Study and team detail",
        sub_title="Research team",
        rubric="OpenSAFELY will need to assess the impact of onboarding your team on our own capacity.",
        fieldsets=[
            fieldset(
                label="Team",
                fields=[
                    field(
                        name="team_details",
                        label="Provide details of the team involved in the proposed research",
                    ),
                ],
            ),
        ],
    ),
    form(
        key=13,
        title="Study and team detail",
        sub_title="Electronic health record (EHR) data",
        rubric=SNIPPET,
        fieldsets=[
            fieldset(
                label="EHR data",
                fields=[
                    field(
                        name="previous_experience_with_ehr",
                        label="Describe your previous experience of working with primary care electronic health record data (e.g. CPRD)",
                    ),
                ],
            ),
        ],
    ),
    form(
        key=14,
        title="Study and team detail",
        sub_title="Software development coding skills",
        rubric=SNIPPET,
        fieldsets=[
            fieldset(
                label="Script-based coding",
                fields=[
                    field(
                        name="evidence_of_coding",
                        label="Provide evidence of you/your research group experience of using a script-based coding language",
                        help_text=SNIPPET,
                    ),
                    field(
                        name="all_applicants_completed_getting_started",
                        label=SNIPPET,
                        help_text=SNIPPET,
                    ),
                ],
            ),
        ],
    ),
    form(
        key=15,
        title="Study and team detail",
        sub_title="Sharing code in the public domain",
        rubric=SNIPPET,
        fieldsets=[
            fieldset(
                label="Sharing analytic code",
                fields=[
                    field(
                        name="evidence_of_sharing_in_public_domain_before",
                        label="Provide evidence of you/your research group sharing and documenting analytic code in the public domain",
                    ),
                ],
            ),
        ],
    ),
]
