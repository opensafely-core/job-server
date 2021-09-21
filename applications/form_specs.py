form_specs = [
    {
        "key": 1,
        "title": "Contact details",
        "sub_title": "Provide the contact information for the overall application owner",
        "rubric": "<snippet>",
        "fieldsets": [
            {
                "label": "Personal details",
                "fields": [
                    {
                        "name": "full_name",
                        "label": "Full name",
                    },
                    {
                        "name": "email",
                        "label": "Email",
                    },
                    {
                        "name": "telephone",
                        "label": "Telephone number",
                    },
                ],
            },
            {
                "label": "Organisation",
                "fields": [
                    {
                        "name": "job_title",
                        "label": "Job title",
                    },
                    {
                        "name": "team_name",
                        "label": "Team or division",
                    },
                    {
                        "name": "organisation",
                        "label": "Organisation",
                    },
                ],
            },
        ],
    },
    {
        "key": 2,
        "title": "Reasons for the request",
        "sub_title": "Study information",
        "rubric": "<snippet>",
        "fieldsets": [
            {
                "label": "Study information",
                "fields": [
                    {
                        "name": "study_name",
                        "label": "Study name",
                        "help_text": "This should be a short public-friendly name.",
                    },
                    {
                        "name": "study_purpose",
                        "label": "What is the purpose for which you are requesting access to the OpenSAFELY data?",
                        "help_text": "<snippet>",
                    },
                ],
            },
        ],
    },
    {
        "key": 3,
        "title": "Reasons for the request",
        "sub_title": "Study purpose",
        "rubric": "<snippet>",
        "fieldsets": [
            {
                "label": "Simple description",
                "fields": [
                    {
                        "name": "description",
                        "label": "Provide a short lay description of your study purpose for the general public",
                    },
                ],
            },
            {
                "label": "Study author",
                "fields": [
                    {
                        "name": "author_name",
                        "label": "Name of application owner",
                    },
                    {
                        "name": "author_email",
                        "label": "Work email address",
                    },
                    {
                        "name": "author_organisation",
                        "label": "Affiliated organisation",
                    },
                ],
            },
        ],
    },
    {
        "key": 4,
        "title": "Reasons for the request",
        "sub_title": "Study data",
        "rubric": "",
        "fieldsets": [
            {
                "label": "Study data",
                "fields": [
                    {
                        "name": "data_meets_purpose",
                        "label": "State how the data you have requested meets your purpose",
                    },
                    {
                        "name": "need_record_level_data",
                        "label": "Are you requesting record level data?",
                    },
                ],
            },
        ],
    },
    {
        "key": 5,
        "title": "Reasons for the request",
        "sub_title": "Record level data",
        "rubric": "",
        "fieldsets": [
            {
                "label": "Record level data",
                "fields": [
                    {
                        "name": "record_level_data_reasons",
                        "label": "Explain why you require access to record level data",
                    },
                ],
            },
        ],
    },
    {
        "key": 6,
        "title": "Reasons for the request",
        "subtitle": "Ethical and sponsor requirements",
        "rubric": "<snippet>",
        "fieldsets": [
            {
                "label": "Type of study",
                "fields": [
                    {
                        "name": "is_study_research",
                        "label": "Research",
                    },
                    {
                        "name": "is_study_service_evaluation",
                        "label": "Service evaluation",
                    },
                    {
                        "name": "is_study_audit",
                        "label": "Audit",
                    },
                ],
            },
        ],
        "can_continue": lambda application: (
            application.is_study_research
            or application.is_study_service_evaluation
            or application.is_study_audit
        ),
        "cant_continue_message": "You must select at least one purpose",
    },
    {
        "key": 7,
        "title": "Reasons for the request",
        "sub_title": "Ethical and sponsor requirements",
        "rubric": "<snippet>",
        "footer": "<snippet>",
        "fieldsets": [
            {
                "label": "HRA REC and Institutional REC",
                "fields": [
                    {
                        "name": "hra_ires_id",
                        "label": "HRA / IRSE ID",
                    },
                    {
                        "name": "hra_rec_reference",
                        "label": "HRA / REC reference",
                    },
                    {
                        "name": "institutional_rec_reference",
                        "label": "Institutional REC reference",
                    },
                ],
            },
        ],
        "prerequisite": lambda application: application.is_study_research,
    },
    {
        "key": 8,
        "title": "Reasons for the request",
        "sub_title": "Ethical and sponsor requirements",
        "rubric": "<snippet>",
        "footer": "<snippet>",
        "fieldsets": [
            {
                "label": "Service evaluation or an audit",
                "fields": [
                    {
                        "name": "institutional_rec_reference",
                        "label": "Institutional REC reference",
                    },
                ],
            },
            {
                "label": "Sponsor details",
                "fields": [
                    {
                        "name": "sponsor_name",
                        "label": "Sponsor name",
                    },
                    {
                        "name": "sponsor_email",
                        "label": "Sponsor email address",
                    },
                    {
                        "name": "sponsor_job_role",
                        "label": "Sponsor job role",
                    },
                ],
            },
        ],
        "prerequisite": lambda application: (
            application.is_study_service_evaluation or application.is_study_audit
        ),
    },
    {
        "key": 9,
        "title": "Reasons for the request",
        "sub_title": "Chief Medical Officer (CMO) priority list",
        "rubric": "",
        "fieldsets": [
            {
                "label": "CMO priority list",
                "fields": [
                    {
                        "name": "is_on_cmo_priority_list",
                        "label": "<snippet>",
                    },
                ],
            },
        ],
    },
    {
        "key": 10,
        "title": "Reasons for the request",
        "sub_title": "Legal basis and common law duty",
        "rubric": "",
        "fieldsets": [
            {
                "label": "Legal basis for record level data",
                "fields": [
                    {
                        "name": "legal_basis_for_accessing_data_under_dpa",
                        "label": "State the legal basis for accessing the data under data protection law",
                        "help_text": "<snippet>",
                    },
                ],
            },
            {
                "label": "Legal basis for record level data",
                "fields": [
                    {
                        "name": "how_is_duty_of_confidentiality_satisfied",
                        "label": "State how you are satisfying or setting aside the common law duty of confidentiality",
                        "help_text": "<snippet>",
                    },
                ],
            },
        ],
    },
    {
        "key": 11,
        "title": "Study and team detail",
        "sub_title": "Study funding",
        "rubric": "<snippet>",
        "fieldsets": [
            {
                "label": "Funding",
                "fields": [
                    {
                        "name": "funding_details",
                        "label": "Provide details of how your research study is funded",
                    },
                ],
            },
        ],
    },
    {
        "key": 12,
        "title": "Study and team detail",
        "sub_title": "Research team",
        "rubric": "OpenSAFELY will need to assess the impact of onboarding your team on our own capacity.",
        "fieldsets": [
            {
                "label": "Team",
                "fields": [
                    {
                        "name": "team_details",
                        "label": "Provide details of the team involved in the proposed research",
                    },
                ],
            },
        ],
    },
    {
        "key": 13,
        "title": "Study and team detail",
        "sub_title": "Electronic health record (EHR) data",
        "rubric": "<snippet>",
        "fieldsets": [
            {
                "label": "EHR data",
                "fields": [
                    {
                        "name": "previous_experience_with_ehr",
                        "label": "Describe your previous experience of working with primary care electronic health record data (e.g. CPRD)",
                    },
                ],
            },
        ],
    },
    {
        "key": 14,
        "title": "Study and team detail",
        "sub_title": "Software development coding skills",
        "rubric": "<snippet>",
        "fieldsets": [
            {
                "label": "Script-based coding",
                "fields": [
                    {
                        "name": "evidence_of_coding",
                        "label": "Provide evidence of you/your research group experience of using a script-based coding language",
                        "help_text": "<snippet>",
                    },
                    {
                        "name": "all_applicants_completed_getting_started",
                        "label": "<snippet>",
                        "help_text": "<snippet>",
                    },
                ],
            },
        ],
    },
    {
        "key": 15,
        "title": "Study and team detail",
        "sub_title": "Sharing code in the public domain",
        "rubric": "<snippet>",
        "fieldsets": [
            {
                "label": "Sharing analytic code",
                "fields": [
                    {
                        "name": "evidence_of_sharing_in_public_domain_before",
                        "label": "Provide evidence of you/your research group sharing and documenting analytic code in the public domain",
                    },
                ],
            },
        ],
    },
]
