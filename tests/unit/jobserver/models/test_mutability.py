import pytest
from django.apps import apps

from jobserver.model_utils import ImmutableError
from tests.paired_fields_utils import get_models


MUTABLE_MODELS = [
    apps.get_model(x)
    for x in [
        "applications.Application",
        "applications.CmoPriorityListPage",
        "applications.CommercialInvolvementPage",
        "applications.ContactDetailsPage",
        "applications.DatasetsPage",
        "applications.LegalBasisPage",
        "applications.PreviousEhrExperiencePage",
        "applications.RecordLevelDataPage",
        "applications.ReferencesPage",
        "applications.ResearcherDetailsPage",
        "applications.ResearcherRegistration",
        "applications.SharingCodePage",
        "applications.SoftwareDevelopmentExperiencePage",
        "applications.SponsorDetailsPage",
        "applications.StudyDataPage",
        "applications.StudyFundingPage",
        "applications.StudyInformationPage",
        "applications.StudyPurposePage",
        "applications.TeamDetailsPage",
        "applications.TypeOfStudyPage",
        "interactive.AnalysisRequest",
        "jobserver.AuditableEvent",
        "jobserver.Backend",
        "jobserver.BackendMembership",
        "jobserver.Job",
        "jobserver.JobRequest",
        "jobserver.Org",
        "jobserver.OrgMembership",
        "jobserver.Project",
        "jobserver.ProjectCollaboration",
        "jobserver.PublishRequest",
        "jobserver.Release",
        "jobserver.ReleaseFile",
        "jobserver.ReleaseFileReview",
        "jobserver.Repo",
        "jobserver.Report",
        "jobserver.Snapshot",
        "jobserver.Stats",
        "jobserver.User",
        "jobserver.Workspace",
        "redirects.Redirect",
    ]
]

IMMUTABLE_MODELS = [
    apps.get_model(x)
    for x in [
        "jobserver.ProjectMembership",
    ]
]

MODEL_METHODS = ["delete", "save"]

QUERYSET_METHODS = [
    "bulk_create",
    "bulk_update",
    "create",
    "delete",
    "get_or_create",
    "update",
    "update_or_create",
]


def test_all_models_are_listed():
    assert set(MUTABLE_MODELS) | set(IMMUTABLE_MODELS) == set(
        get_models()
    ), "The lists of mutable and immutable models are incomplete"


def test_all_models_are_listed_as_either_mutable_or_immutable():
    assert (
        set(MUTABLE_MODELS) & set(IMMUTABLE_MODELS) == set()
    ), "A model must be listed as either mutable or immutable"


@pytest.mark.parametrize("Model", MUTABLE_MODELS)
@pytest.mark.parametrize("method", MODEL_METHODS)
def test_mutable_model_methods(Model, method):
    try:
        getattr(Model(), method)()
    except Exception as e:
        assert type(e) != ImmutableError
    else:
        assert True


@pytest.mark.parametrize("Model", IMMUTABLE_MODELS)
@pytest.mark.parametrize("method", MODEL_METHODS)
def test_immutable_model_methods(Model, method):
    with pytest.raises(ImmutableError):
        getattr(Model(), method)()
