import pytest
from django.db import IntegrityError

from ....factories import OrgFactory, ProjectCollaborationFactory, ProjectFactory


def test_projectcollaboration_only_one_lead_org():
    project = ProjectFactory()

    ProjectCollaborationFactory.create_batch(3, project=project)
    ProjectCollaborationFactory(project=project, is_lead=True)

    with pytest.raises(IntegrityError):
        ProjectCollaborationFactory(project=project, is_lead=True)


def test_projectcollaboration_str():
    project = ProjectFactory(name="Project 7")

    datalab = OrgFactory(name="Datalab")
    collaboration = ProjectCollaborationFactory(project=project, org=datalab)
    assert str(collaboration) == "Datalab <-> Project 7"

    bennett = OrgFactory(name="Bennett")
    collaboration = ProjectCollaborationFactory(
        project=project, org=bennett, is_lead=True
    )
    assert str(collaboration) == "Bennett <-> Project 7 (lead)"
