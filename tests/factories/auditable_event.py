import factory

from jobserver.models import AuditableEvent


class AuditableEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AuditableEvent
