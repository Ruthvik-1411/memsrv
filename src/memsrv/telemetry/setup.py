"""Sets up tracer provider + exporters"""
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from config import MemoryConfig

logger = logging.getLogger(__name__)

def setup_tracer(config: MemoryConfig) -> trace.Tracer | None:
    """Sets up a global OTEL tracer if enabled"""
    if not config.ENABLE_OTEL:
        logger.info("OpenTelemetry disabled (ENABLE_OTEL=False).")
        return None

    try:
        resource = Resource.create({
            "service.name": config.OTEL_SERVICE_NAME or "memsrv",
        })

        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

        # Console exporter for local dev
        # TODO: Disable when deploying, don't want this many logs
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

        # OTLP exporter if endpoint exists, local/deployed
        if config.OTEL_EXPORTER_OTLP_ENDPOINT:
            otlp_exporter = OTLPSpanExporter(
                endpoint=config.OTEL_EXPORTER_OTLP_ENDPOINT,
                headers=_parse_headers(config.OTEL_EXPORTER_OTLP_HEADERS)
                if config.OTEL_EXPORTER_OTLP_HEADERS else None
            )
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info("OTLP exporter configured successfully.")

        logger.info("OpenTelemetry tracer initialized.")
        return trace.get_tracer(config.OTEL_SERVICE_NAME or "memsrv")

    except Exception as e:
        logger.warning(f"Failed to initialize OpenTelemetry: {e}. Tracing disabled.")
        return None

def _parse_headers(header_str: str) -> dict:
    """Parses headers: 'key1=val1,key2=val2'to {'key1': 'val1', 'key2': 'val2'}"""
    try:
        return dict(item.split("=", 1) for item in header_str.split(","))
    except Exception:
        logger.warning("Invalid OTEL_EXPORTER_OTLP_HEADERS format.")
        return {}
