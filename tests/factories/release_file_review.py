import factory

from jobserver.models import ReleaseFileReview


class ReleaseFileReviewFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ReleaseFileReview

    created_by = factory.SubFactory("tests.factories.UserFactory")
    release_file = factory.SubFactory("tests.factories.ReleaseFileFactory")
