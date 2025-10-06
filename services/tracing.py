import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


def get_provider():
    # https://github.com/open-telemetry/semantic-conventions/tree/main/docs/resource#service
    resource = Resource.create(
        attributes={"service.name": os.environ.get("OTEL_SERVICE_NAME", "job-server")}
    )
    return TracerProvider(resource=resource)


def add_exporter(provider, exporter, processor=BatchSpanProcessor):
    """Utility method to add an exporter.

    We use the BatchSpanProcessor by default, which is the default for
    production. This is asynchronous, and queues and retries sending telemetry.

    In testing, we instead use SimpleSpanProcessor, which is synchronous and
    easy to inspect the output of within a test.
    """
    # Note: BatchSpanProcessor is configured via env vars:
    # https://opentelemetry-python.readthedocs.io/en/latest/sdk/trace.export.html#opentelemetry.sdk.trace.export.BatchSpanProcessor
    provider.add_span_processor(processor(exporter))


def setup_default_tracing(set_global=True):
    provider = get_provider()

    if "OTEL_EXPORTER_OTLP_ENDPOINT" in os.environ:
        add_exporter(provider, OTLPSpanExporter())

    if os.environ.get("OTEL_EXPORTER_CONSOLE", "").lower() == "true":
        add_exporter(provider, ConsoleSpanExporter())

    if set_global:  # pragma: nocover
        trace.set_tracer_provider(provider)
    # bug: this code requires some envvars to be set, so ensure they are
    os.environ.setdefault("PYTHONPATH", "")
    from opentelemetry.instrumentation.auto_instrumentation import (  # noqa: F401
        sitecustomize,
    )

    return provider
