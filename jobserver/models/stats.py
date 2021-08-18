from django.db import models


class Stats(models.Model):
    """This holds per-Backend, per-URL API statistics."""

    backend = models.ForeignKey(
        "Backend", on_delete=models.PROTECT, related_name="stats"
    )

    api_last_seen = models.DateTimeField(null=True, blank=True)
    url = models.TextField()

    class Meta:
        unique_together = ["backend", "url"]

    def __str__(self):
        backend = self.backend.slug
        last_seen = (
            self.api_last_seen.strftime("%Y-%m-%d %H:%M:%S")
            if self.api_last_seen
            else "never"
        )
        return f"{backend} | {last_seen} | {self.url}"
