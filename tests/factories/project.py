import factory

from jobserver.models import Project


def _project_collaboration_factory(obj, create, extracted, **kwargs):
    from . import ProjectCollaborationFactory

    if not create or not extracted:
        # Simple build, or nothing to add, do nothing.
        return

    # Add the iterable of groups using bulk addition
    for org in extracted:
        ProjectCollaborationFactory(org=org, project=obj, is_lead=True)


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project
        skip_postgeneration_save = True

    created_by = factory.SubFactory("tests.factories.UserFactory")
    updated_by = factory.SubFactory("tests.factories.UserFactory")

    name = factory.Sequence(lambda n: f"Project {n}")
    slug = factory.Sequence(lambda n: f"project-{n}")

    orgs = factory.PostGeneration(_project_collaboration_factory)
