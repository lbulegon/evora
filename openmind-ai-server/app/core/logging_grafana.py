"""
Sistema de Logging estruturado para Grafana/Loki
Gera logs em formato JSON compatível com Loki
"""
import logging
import logging.handlers
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """Formatter que converte logs para JSON estruturado (compatível com Loki)"""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formata log record para JSON estruturado
        Compatível com Grafana Loki
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "file": record.filename,
        }
        
        # Adicionar campos extras se existirem
        if hasattr(record, 'request_id'):
            log_data["request_id"] = record.request_id
        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id
        if hasattr(record, 'ip_address'):
            log_data["ip_address"] = record.ip_address
        if hasattr(record, 'endpoint'):
            log_data["endpoint"] = record.endpoint
        if hasattr(record, 'method'):
            log_data["method"] = record.method
        if hasattr(record, 'status_code'):
            log_data["status_code"] = record.status_code
        if hasattr(record, 'processing_time_ms'):
            log_data["processing_time_ms"] = record.processing_time_ms
        if hasattr(record, 'image_size_bytes'):
            log_data["image_size_bytes"] = record.image_size_bytes
        if hasattr(record, 'api_provider'):
            log_data["api_provider"] = record.api_provider
        
        # Adicionar exception info se houver
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            log_data["exception_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
        
        # Adicionar stack trace para DEBUG
        if record.levelno == logging.DEBUG and hasattr(record, 'stack_info') and record.stack_info:
            log_data["stack"] = record.stack_info
        
        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Formatter tradicional para logs legíveis"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


def setup_grafana_logging():
    """
    Configura sistema de logging para Grafana/Loki
    - Logs estruturados em JSON
    - Arquivos rotativos em /var/log/openmind-ai
    - Compatível com Promtail para ingestão no Loki
    """
    # Diretório de logs
    if os.path.exists("/var/log"):
        log_dir = Path(settings.LOG_DIR if hasattr(settings, 'LOG_DIR') else "/var/log/openmind-ai")
    else:
        log_dir = Path("logs")
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Nível de log
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Escolher formatter baseado na configuração
    use_json = getattr(settings, 'LOG_FORMAT', 'json').lower() == 'json'
    formatter = JSONFormatter() if use_json else TextFormatter()
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    
    # Handler para log geral (app.log)
    app_log_file = log_dir / "app.log"
    app_handler = logging.handlers.RotatingFileHandler(
        app_log_file,
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=10,
        encoding='utf-8'
    )
    app_handler.setLevel(log_level)
    app_handler.setFormatter(formatter)
    root_logger.addHandler(app_handler)
    
    # Handler para erros (errors.log) - apenas ERROR e CRITICAL
    error_log_file = log_dir / "errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=20,  # Manter mais backups de erros
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # Handler para console (desenvolvimento)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    # Console sempre usa formato texto (mais legível)
    console_handler.setFormatter(TextFormatter())
    root_logger.addHandler(console_handler)
    
    # Logger específico para access logs (requests HTTP)
    access_logger = logging.getLogger("access")
    access_log_file = log_dir / "access.log"
    access_handler = logging.handlers.RotatingFileHandler(
        access_log_file,
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=10,
        encoding='utf-8'
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(formatter)
    access_logger.addHandler(access_handler)
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False
    
    # Logger específico para análise de imagens
    analysis_logger = logging.getLogger("analysis")
    analysis_log_file = log_dir / "analysis.log"
    analysis_handler = logging.handlers.RotatingFileHandler(
        analysis_log_file,
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=15,
        encoding='utf-8'
    )
    analysis_handler.setLevel(logging.INFO)
    analysis_handler.setFormatter(formatter)
    analysis_logger.addHandler(analysis_handler)
    analysis_logger.setLevel(logging.INFO)
    analysis_logger.propagate = False
    
    # Logger para métricas/performance
    metrics_logger = logging.getLogger("metrics")
    metrics_log_file = log_dir / "metrics.log"
    metrics_handler = logging.handlers.RotatingFileHandler(
        metrics_log_file,
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=10,
        encoding='utf-8'
    )
    metrics_handler.setLevel(logging.INFO)
    metrics_handler.setFormatter(formatter)
    metrics_logger.addHandler(metrics_handler)
    metrics_logger.setLevel(logging.INFO)
    metrics_logger.propagate = False
    
    # Log inicial
    logger = logging.getLogger(__name__)
    logger.info(
        "Sistema de Logging Grafana/Loki Inicializado",
        extra={
            "log_dir": str(log_dir.absolute()),
            "log_level": settings.LOG_LEVEL,
            "log_format": "JSON" if use_json else "TEXT",
            "loki_enabled": getattr(settings, 'LOKI_ENABLED', True)
        }
    )
    
    return log_dir


def get_logger(name: str) -> logging.Logger:
    """Retorna um logger configurado"""
    return logging.getLogger(name)


def log_request(logger: logging.Logger, request_id: str, method: str, 
                endpoint: str, status_code: int, processing_time_ms: int,
                ip_address: Optional[str] = None, **kwargs):
    """Log estruturado de requisição HTTP"""
    logger.info(
        f"{method} {endpoint} - {status_code} - {processing_time_ms}ms",
        extra={
            "request_id": request_id,
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "processing_time_ms": processing_time_ms,
            "ip_address": ip_address,
            **kwargs
        }
    )


def log_analysis(logger: logging.Logger, request_id: str, image_filename: str,
                 image_size_bytes: int, processing_time_ms: int, 
                 api_provider: str, success: bool, **kwargs):
    """Log estruturado de análise de imagem"""
    level = logging.INFO if success else logging.ERROR
    logger.log(
        level,
        f"Análise de imagem: {image_filename} - {api_provider} - {processing_time_ms}ms",
        extra={
            "request_id": request_id,
            "image_filename": image_filename,
            "image_size_bytes": image_size_bytes,
            "processing_time_ms": processing_time_ms,
            "api_provider": api_provider,
            "success": success,
            **kwargs
        }
    )



