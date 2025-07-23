from django_extensions.management.jobs import MinutelyJob


class Job(MinutelyJob):
    help = "Call the rap-controller status endpoint and log the results"  # noqa: A003

    def execute(self):
        pass
