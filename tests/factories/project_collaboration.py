import factory

from jobserver.models import ProjectCollaboration


class ProjectCollaborationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProjectCollaboration

    created_by = factory.SubFactory("tests.factories.UserFactory")
    org = factory.SubFactory("tests.factories.OrgFactory")
    project = factory.SubFactory("tests.factories.ProjectFactory")
    updated_by = factory.SubFactory("tests.factories.UserFactory")
