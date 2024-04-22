from django.urls import path

from .views import airlock_event_view


app_name = "airlock"

urlpatterns = [
    path("events/", airlock_event_view, name="airlock_event"),
]
