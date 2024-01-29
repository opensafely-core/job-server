from datetime import UTC, datetime

import factory
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from jobserver.models import Job


def generate_traceparent():
    """Generate an OTel trace context, as would be passed up from job-runner."""
    ctx = {}
    tracer = trace.get_tracer("jobs")
    root = tracer.start_span("JOB")

    with trace.use_span(root, end_on_exit=False):
        TraceContextTextMapPropagator().inject(ctx)

    return ctx


class JobFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Job

    job_request = factory.SubFactory("tests.factories.JobRequestFactory")

    identifier = factory.Sequence(lambda n: f"identifier-{n}")

    updated_at = factory.fuzzy.FuzzyDateTime(datetime(2020, 1, 1, tzinfo=UTC))

    trace_context = factory.LazyFunction(generate_traceparent)
