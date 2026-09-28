import logging
import sys

from opentelemetry import trace
from pythonjsonlogger import json


class TraceIdFilter(logging.Filter):
    """Injeta o trace_id do OpenTelemetry em todos os logs."""
    def filter(self, record):
        span = trace.get_current_span()
        if span.is_recording():
            record.trace_id = format(span.get_span_context().trace_id, '032x')
            record.span_id = format(span.get_span_context().span_id, '016x')
        else:
            record.trace_id = None
            record.span_id = None
        return True

def setup_json_logger(name: str = "orchestrator") -> logging.Logger:
    """Configura um logger que formata a saída em JSON para o Loki."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        # Define os campos que queremos no JSON final
        formatter = json.JsonFormatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s %(trace_id)s %(span_id)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Adiciona o filtro que injeta o trace_id no contexto
        logger.addFilter(TraceIdFilter())
        logger.propagate = False

    return logger