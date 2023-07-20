import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from services.logging import logging_config_dict


# Where to log to (stdout and stderr)
accesslog = "-"
errorlog = "-"

# Configure log structure
# http://docs.gunicorn.org/en/stable/settings.html#logconfig-dict
logconfig_dict = logging_config_dict

# workers
workers = 5

# listen
port = 8000
bind = "0.0.0.0"


def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

    resource = Resource.create(attributes={"service.name": "job-server"})

    trace.set_tracer_provider(TracerProvider(resource=resource))

    if "OTEL_EXPORTER_OTLP_ENDPOINT" in os.environ:
        span_processor = BatchSpanProcessor(OTLPSpanExporter())
        trace.get_tracer_provider().add_span_processor(span_processor)

    from opentelemetry.instrumentation.auto_instrumentation import (  # noqa: F401
        sitecustomize,
    )
