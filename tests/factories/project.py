from collections import abc

import factory

from jobserver.models import Project


def _project_collaboration_factory(obj, create, extracted, **kwargs):
    from . import ProjectCollaborationFactory

    if not create or not extracted:
        # Simple build, or nothing to add, do nothing.
        return

    extracted = extracted if isinstance(extracted, abc.Iterable) else [extracted]

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

    org = factory.PostGeneration(_project_collaboration_factory)
    orgs = factory.PostGeneration(_project_collaboration_factory)


class ProjectDataFactory(factory.Factory):
    """
    Generate a default data dict for post requests to the ProjectCreateForm.

    By default:
    - Returns a valid data dict:
        data = {
            "name": "test1",
            "number": "1234567832",
            "orgs": ["1"],
            "copilot": "1",
        }
    - Will create an org & a user (copilot) instance in the db.
      Use .build() in tests where you don't want this behaviour.
    """

    class Meta:
        model = dict

    name = factory.Sequence(lambda n: f"Test Project {n}")
    number = factory.Sequence(lambda n: str(1000000 + n))

    @factory.lazy_attribute
    def orgs(self):
        from tests.factories.org import OrgFactory

        org = OrgFactory()
        return [str(org.pk)]

    @factory.lazy_attribute
    def copilot(self):
        from tests.factories.user import UserFactory

        user = UserFactory()
        return str(user.pk)
