import os

import opentelemetry.exporter.otlp.proto.http.trace_exporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import ConsoleSpanExporter

from services.tracing import setup_default_tracing


def test_setup_default_tracing_empty_env(monkeypatch):
    env = {"PYTHONPATH": ""}
    monkeypatch.setattr(os, "environ", env)
    provider = setup_default_tracing(set_global=False)
    assert provider._active_span_processor._span_processors == ()


def test_setup_default_tracing_console(monkeypatch):
    env = {"PYTHONPATH": "", "OTEL_EXPORTER_CONSOLE": "true"}
    monkeypatch.setattr(os, "environ", env)
    provider = setup_default_tracing(set_global=False)

    processor = provider._active_span_processor._span_processors[0]
    assert isinstance(processor.span_exporter, ConsoleSpanExporter)


def test_setup_default_tracing_otlp_with_env(monkeypatch):
    env = {
        "PYTHONPATH": "",
        "OTEL_EXPORTER_OTLP_HEADERS": "foo=bar",
        "OTEL_SERVICE_NAME": "service",
        "OTEL_EXPORTER_OTLP_ENDPOINT": "https://endpoint",
    }
    monkeypatch.setattr(os, "environ", env)
    monkeypatch.setattr(
        opentelemetry.exporter.otlp.proto.http.trace_exporter, "environ", env
    )
    provider = setup_default_tracing(set_global=False)
    assert provider.resource.attributes["service.name"] == "service"

    exporter = provider._active_span_processor._span_processors[0].span_exporter

    assert isinstance(exporter, OTLPSpanExporter)
    assert exporter._endpoint == "https://endpoint/v1/traces"
    assert exporter._headers == {"foo": "bar"}
