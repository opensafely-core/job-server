from ....factories import OrgFactory, ProjectCollaborationFactory, ProjectFactory


def test_projectmembership_str():
    org = OrgFactory(name="Bennett")
    project = ProjectFactory(name="Project 7")

    collaboration = ProjectCollaborationFactory(project=project, org=org)
    assert str(collaboration) == "Bennett <-> Project 7"

    collaboration = ProjectCollaborationFactory(project=project, org=org, is_lead=True)
    assert str(collaboration) == "Bennett <-> Project 7 (lead)"
