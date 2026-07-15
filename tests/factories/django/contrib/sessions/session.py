from datetime import timedelta

import factory
from django.contrib.sessions.models import Session
from django.utils import timezone


class SessionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Session

    session_key = "test_session_key"
    session_data = "test_session_data"
    expire_date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=1))
