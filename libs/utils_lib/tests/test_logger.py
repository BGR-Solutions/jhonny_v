import io
import json
import logging
from unittest.mock import MagicMock, patch

import pytest
from pythonjsonlogger.json import JsonFormatter

# Ajuste o import conforme a estrutura real do seu projeto
from src.logger import TraceIdFilter, setup_json_logger


def test_trace_id_filter_no_active_span():
    """Testa o comportamento do filtro quando não há um span ativo (ex: log fora de requisição)."""
    log_filter = TraceIdFilter()
    record = logging.LogRecord("test", logging.INFO, "path", 1, "test message", None, None)
    
    # Mock do OpenTelemetry para simular que NÃO estamos gravando um trace
    with patch("src.utils.logger.trace.get_current_span") as mock_get_span:
        mock_span = MagicMock()
        mock_span.is_recording.return_value = False
        mock_get_span.return_value = mock_span
        
        resultado = log_filter.filter(record)
        
        assert resultado is True
        assert record.trace_id is None
        assert record.span_id is None


def test_trace_id_filter_with_active_span():
    """Testa se o filtro injeta corretamente os IDs hexadecimais quando há um trace ativo."""
    log_filter = TraceIdFilter()
    record = logging.LogRecord("test", logging.INFO, "path", 1, "test message", None, None)
    
    with patch("src.utils.logger.trace.get_current_span") as mock_get_span:
        mock_span = MagicMock()
        mock_span.is_recording.return_value = True
        
        # Simulando IDs inteiros gerados pelo OpenTelemetry
        mock_context = MagicMock()
        mock_context.trace_id = 12345678901234567890
        mock_context.span_id = 9876543210
        mock_span.get_span_context.return_value = mock_context
        
        mock_get_span.return_value = mock_span
        
        resultado = log_filter.filter(record)
        
        assert resultado is True
        # Verifica se formatou com 32 caracteres (trace) e 16 caracteres (span)
        assert record.trace_id == format(mock_context.trace_id, '032x')
        assert record.span_id == format(mock_context.span_id, '016x')


def test_setup_json_logger_configuration():
    """Valida se o logger é construído com os handlers, formatadores e filtros corretos."""
    logger_name = "test_config_logger"
    
    # Limpa handlers residuais caso existam
    logging.getLogger(logger_name).handlers.clear()
    
    logger = setup_json_logger(logger_name)
    
    assert logger.name == logger_name
    assert logger.level == logging.INFO
    assert logger.propagate is False
    assert len(logger.handlers) == 1
    
    handler = logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert isinstance(handler.formatter, JsonFormatter)
    
    # Verifica se o nosso filtro customizado foi adicionado
    has_trace_filter = any(isinstance(f, TraceIdFilter) for f in logger.filters)
    assert has_trace_filter is True


def test_logger_json_output():
    """Faz um teste ponta-a-ponta garantindo que a saída no stdout é um JSON válido."""
    logger_name = "test_output_logger"
    logging.getLogger(logger_name).handlers.clear()
    
    # Redirecionamos o sys.stdout para a memória para conseguirmos capturar o que foi "impresso"
    mock_stdout = io.StringIO()
    
    with patch("sys.stdout", mock_stdout):
        logger = setup_json_logger(logger_name)
        
        # Mockamos o span para evitar erros de ausência do OpenTelemetry
        with patch("src.utils.logger.trace.get_current_span") as mock_get_span:
            mock_span = MagicMock()
            mock_span.is_recording.return_value = False
            mock_get_span.return_value = mock_span
            
            # Emitimos um log real
            logger.info("Mensagem de teste Jhonny-V")

    # Extrai a string impressa
    output = mock_stdout.getvalue()
    
    # Tenta transformar a string num dicionário JSON
    try:
        log_dict = json.loads(output)
    except json.JSONDecodeError:
        pytest.fail("A saída do logger não é um JSON válido!")
        
    assert log_dict["message"] == "Mensagem de teste Jhonny-V"
    assert log_dict["levelname"] == "INFO"
    assert log_dict["name"] == logger_name
    assert "trace_id" in log_dict
    assert log_dict["trace_id"] is None