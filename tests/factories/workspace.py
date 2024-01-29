import factory
import factory.fuzzy

from jobserver.models import Workspace


class WorkspaceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Workspace

    project = factory.SubFactory("tests.factories.ProjectFactory")
    repo = factory.SubFactory("tests.factories.RepoFactory")
    created_by = factory.SubFactory("tests.factories.UserFactory")
    updated_by = factory.SubFactory("tests.factories.UserFactory")

    name = factory.Sequence(lambda n: f"workspace-{n}")
