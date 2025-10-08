"""Sets up tracer provider + exporters"""
import os
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

logger = logging.getLogger(__name__)

def setup_tracer(service_name: str = "memsrv"):
    """Sets up a global OTEL tracer if enabled.

    Returns:
        tracer (trace.Tracer or None)
    """
    # TODO: read from config file
    if os.getenv("ENABLE_OTEL", "false").lower() not in ("1", "true", "yes"):
        logger.info("OpenTelemetry disabled (ENABLE_OTEL is not set).")
        return None

    try:
        resource = Resource.create({
            "service.name": service_name,
        })

        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

        # Console exporter for local dev
        # TODO: Disable when deploying
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

        # OTLP exporter if endpoint exists, local/deployed
        if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
            otlp_exporter = OTLPSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info("OTLP exporter configured successfully.")

        logger.info("OpenTelemetry tracer initialized.")
        return trace.get_tracer(service_name)

    except Exception as e:
        logger.warning(f"Failed to initialize OpenTelemetry: {e}. Tracing disabled.")
        return None
