import factory
from social_django.models import UserSocialAuth


class UserSocialAuthFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserSocialAuth

    provider = "github"
    uid = factory.Sequence(lambda n: f"uid-{n}")
    user = factory.SubFactory("tests.factories.UserFactory")
