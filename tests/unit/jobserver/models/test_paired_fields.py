import pytest
from django.db import IntegrityError
from django.utils import timezone

from jobserver.model_utils import get_models
from tests.factories import UserFactory
from tests.paired_fields_utils import (
    get_all_paired_fields,
    get_optional_paired_fields,
)


"""
The tests in this module test paired fields: two fields with different suffixes that
share a stem. The most common paired fields are "at" and "by" fields, such as
`Repo.internal_signed_off_at` and `Repo.internal_signed_off_by`. In this example, the
different suffixes "_at" and "_by" share the stem "internal_signed_off".

Paired fields are important because of their constraints. In the following table, rows
represent values of one field in a pair; columns represent values of the other field in
the pair. "Pass" indicates that we expect the model to save (i.e. the constraints should
pass); "fail" indicates that we don't expect the model to save, and that we expect an
`IntegrityError` to be raised (i.e. the constraints should fail).

        | None     | Value |
|-------|----------|-------|
| None  | pass*    | fail  |
| Value | fail     | pass  |

*Only when both fields are optional.

In this module, we often need to provide collections of models and fields. For
convenience, we do so with a list of tuples. The first item in the tuple is the model
label, which is a string. The remaining items in the tuple are the field names, which
are also strings. If only the model label is given, then all field names are assumed.
"""

# Several tests rely on models having factories. We explicitly ignore those that don't.
MODELS_WITHOUT_FACTORIES = [
    ("applications.CmoPriorityListPage",),
    ("applications.LegalBasisPage",),
    ("jobserver.ProjectMembership",),
]


@pytest.mark.slow_test
@pytest.mark.parametrize("model", get_models())
@pytest.mark.parametrize("lsuffix,rsuffix", [("_at", "_by")])
def test_fields_are_paired(model, lsuffix, rsuffix):
    """
    Many fields look like they are paired, but (sadly) aren't. Rather than maintain a
    list of paired fields (includes), which is error-prone, we maintain an list of
    unpaired fields (excludes).

    If a new field is added, and the new field looks like it is paired, then this test
    will fail. Either add another new field or exclude the new field.
    """
    names = [
        name
        for field in model._meta.fields
        if (name := field.name)
        not in MODEL_TO_UNPAIRED_FIELDS.get(model._meta.label, set())
    ]

    def get_stems(suffix):
        return {stem for name in names if (stem := name.removesuffix(suffix)) != name}

    lstems = get_stems(lsuffix)
    rstems = get_stems(rsuffix)

    unpaired_lnames = [f"{stem}{lsuffix}" for stem in lstems - rstems]
    unpaired_rnames = [f"{stem}{rsuffix}" for stem in rstems - lstems]
    unpaired_names = sorted(unpaired_lnames + unpaired_rnames)

    assert (
        not unpaired_names
    ), f"{model._meta.label} is missing paired fields for: {', '.join(unpaired_names)}"


@pytest.mark.slow_test
@pytest.mark.parametrize(
    "factory,at_name,by_name",
    get_all_paired_fields(
        "_at",
        "_by",
        exclude=[
            ("jobserver.PublishRequest", "decision_at", "decision_by", "decision"),
            # Missing ReleaseFileReviewFactory.comments
            ("jobserver.ReleaseFileReview",),
            # Missing RedirectFactory.analysis_request
            ("redirects.Redirect",),
        ]
        + MODELS_WITHOUT_FACTORIES,
    ),
)
def test_both_fields_set(factory, at_name, by_name):
    """
    Test the Value/Value case (success).
    """
    factory(**{at_name: timezone.now(), by_name: UserFactory()})


@pytest.mark.slow_test
@pytest.mark.parametrize(
    "factory,at_name,by_name",
    get_optional_paired_fields(
        "_at",
        "_by",
        exclude=[
            # Missing RedirectFactory.analysis_request
            ("redirects.Redirect",),
        ]
        + MODELS_WITHOUT_FACTORIES,
    ),
)
def test_neither_field_set(factory, at_name, by_name):
    """
    Test the None/None case (success), only when both fields are optional.
    """
    factory(**{at_name: None, by_name: None})


@pytest.mark.slow_test
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "factory,at_name,by_name",
    get_all_paired_fields(
        "_at",
        "_by",
        exclude=[
            # "at" has auto_now=True
            ("interactive.AnalysisRequest", "updated_at", "updated_by"),
            ("jobserver.Project", "updated_at", "updated_by"),
            ("jobserver.PublishRequest", "updated_at", "updated_by"),
            ("jobserver.Report", "updated_at", "updated_by"),
            ("jobserver.Workspace", "updated_at", "updated_by"),
        ]
        + MODELS_WITHOUT_FACTORIES,
    ),
)
def test_at_field_not_set_and_by_field_set(factory, at_name, by_name):
    """
    Test the None/Value case (fail).
    """
    with pytest.raises(IntegrityError):
        factory(**{at_name: None, by_name: UserFactory()})


@pytest.mark.slow_test
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "factory,at_name,by_name",
    get_all_paired_fields(
        "_at",
        "_by",
        exclude=[
            # "at" is required but "by" is optional
            ("jobserver.BackendMembership", "created_at", "created_by"),
            ("jobserver.Org", "created_at", "created_by"),
            ("jobserver.OrgMembership", "created_at", "created_by"),
        ]
        + MODELS_WITHOUT_FACTORIES,
    ),
)
def test_at_field_set_and_by_field_not_set(factory, at_name, by_name):
    """
    Test the Value/None case (fail).
    """
    with pytest.raises(IntegrityError):
        factory(**{at_name: timezone.now(), by_name: None})


UNPAIRED_FIELDS = [
    ("applications.Application", "completed_at"),
    (
        "applications.CmoPriorityListPage",
        "created_at",
        "last_reviewed_at",
        "reviewed_by",
        "updated_at",
    ),
    (
        "applications.CommercialInvolvementPage",
        "created_at",
        "last_reviewed_at",
        "reviewed_by",
        "updated_at",
    ),
    (
        "applications.ContactDetailsPage",
        "created_at",
        "last_reviewed_at",
        "reviewed_by",
        "updated_at",
    ),
    (
        "applications.DatasetsPage",
        "created_at",
        "last_reviewed_at",
        "reviewed_by",
        "updated_at",
    ),
    (
        "applications.LegalBasisPage",
        "created_at",
        "last_reviewed_at",
        "reviewed_by",
        "updated_at",
    ),
    (
        "applications.PreviousEhrExperiencePage",
        "created_at",
        "last_reviewed_at",
        "reviewed_by",
        "updated_at",
    ),
    (
        "applications.RecordLevelDataPage",
        "created_at",
        "last_reviewed_at",
        "reviewed_by",
        "updated_at",
    ),
    (
        "applications.ReferencesPage",
        "created_at",
        "last_reviewed_at",
        "reviewed_by",
        "updated_at",
    ),
    (
        "applications.ResearcherDetailsPage",
        "created_at",
        "last_reviewed_at",
        "reviewed_by",
        "updated_at",
    ),
    ("applications.ResearcherRegistration", "created_at", "training_passed_at"),
    (
        "applications.SharingCodePage",
        "created_at",
        "last_reviewed_at",
        "reviewed_by",
        "updated_at",
    ),
    (
        "applications.ShortDataReportPage",
        "created_at",
        "last_reviewed_at",
        "reviewed_by",
        "updated_at",
    ),
    (
        "applications.SoftwareDevelopmentExperiencePage",
        "created_at",
        "last_reviewed_at",
        "reviewed_by",
        "updated_at",
    ),
    (
        "applications.SponsorDetailsPage",
        "created_at",
        "last_reviewed_at",
        "reviewed_by",
        "updated_at",
    ),
    (
        "applications.StudyDataPage",
        "created_at",
        "last_reviewed_at",
        "reviewed_by",
        "updated_at",
    ),
    (
        "applications.StudyFundingPage",
        "created_at",
        "last_reviewed_at",
        "reviewed_by",
        "updated_at",
    ),
    (
        "applications.StudyInformationPage",
        "created_at",
        "last_reviewed_at",
        "reviewed_by",
        "updated_at",
    ),
    (
        "applications.StudyPurposePage",
        "created_at",
        "last_reviewed_at",
        "reviewed_by",
        "updated_at",
    ),
    (
        "applications.TeamDetailsPage",
        "created_at",
        "last_reviewed_at",
        "reviewed_by",
        "updated_at",
    ),
    (
        "applications.TypeOfStudyPage",
        "created_at",
        "last_reviewed_at",
        "reviewed_by",
        "updated_at",
    ),
    ("jobserver.Backend", "created_at", "updated_at"),
    ("jobserver.Job", "completed_at", "created_at", "started_at", "updated_at"),
    ("jobserver.Project", "copilot_support_ends_at"),
    ("jobserver.ReleaseFile", "uploaded_at"),
    ("jobserver.User", "created_by", "login_token_expires_at", "pat_expires_at"),
    ("redirects.Redirect", "expires_at", "updated_at"),
]

MODEL_TO_UNPAIRED_FIELDS = {model: set(fields) for model, *fields in UNPAIRED_FIELDS}
