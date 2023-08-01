import factory

from redirects.models import Redirect


class RedirectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Redirect

    created_by = factory.SubFactory("tests.factories.UserFactory")

    old_url = "/"
