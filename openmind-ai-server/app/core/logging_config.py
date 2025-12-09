"""
Sistema de Logging para OpenMind AI Server (SinapUm)
Configura logs em arquivos locais no servidor
"""
import logging
import logging.handlers
import os
from pathlib import Path
from app.core.config import settings


def setup_logging():
    """
    Configura sistema de logging para o servidor SinapUm
    Cria diretório de logs se não existir e configura handlers de arquivo
    """
    # Diretório de logs - usar /var/log/openmind-ai no servidor, logs/ localmente
    if os.path.exists("/var/log"):
        log_dir = Path("/var/log/openmind-ai")
    else:
        # Para desenvolvimento local
        log_dir = Path("logs")
    
    # Criar diretório se não existir
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configurar nível de log
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Formato de log detalhado
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para log geral da aplicação
    app_log_file = log_dir / "app.log"
    app_handler = logging.handlers.RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    app_handler.setLevel(log_level)
    app_handler.setFormatter(log_format)
    app_handler.set_name("app_file")
    
    # Handler para erros (apenas ERROR e CRITICAL)
    error_log_file = log_dir / "errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,  # Manter mais backups de erros
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(log_format)
    error_handler.set_name("error_file")
    
    # Handler para console (apenas em desenvolvimento)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(
        '%(levelname)s - %(name)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    console_handler.setFormatter(console_format)
    console_handler.set_name("console")
    
    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Limpar handlers existentes
    root_logger.handlers.clear()
    
    # Adicionar handlers
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)
    
    # Logger específico para requests/access
    access_logger = logging.getLogger("access")
    access_log_file = log_dir / "access.log"
    access_handler = logging.handlers.RotatingFileHandler(
        access_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    access_handler.setLevel(logging.INFO)
    access_format = logging.Formatter(
        '%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    access_handler.setFormatter(access_format)
    access_logger.addHandler(access_handler)
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False
    
    # Logger específico para análise de imagens
    analysis_logger = logging.getLogger("analysis")
    analysis_log_file = log_dir / "analysis.log"
    analysis_handler = logging.handlers.RotatingFileHandler(
        analysis_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    analysis_handler.setLevel(logging.INFO)
    analysis_handler.setFormatter(log_format)
    analysis_logger.addHandler(analysis_handler)
    analysis_logger.setLevel(logging.INFO)
    analysis_logger.propagate = False
    
    # Log inicial
    logger = logging.getLogger(__name__)
    logger.info("="*60)
    logger.info("Sistema de Logging Inicializado")
    logger.info(f"Diretório de logs: {log_dir.absolute()}")
    logger.info(f"Nível de log: {settings.LOG_LEVEL}")
    logger.info(f"Arquivos de log:")
    logger.info(f"  - app.log: {app_log_file.absolute()}")
    logger.info(f"  - errors.log: {error_log_file.absolute()}")
    logger.info(f"  - access.log: {access_log_file.absolute()}")
    logger.info(f"  - analysis.log: {analysis_log_file.absolute()}")
    logger.info("="*60)
    
    return log_dir


def get_log_file_path(log_type: str = "app") -> str:
    """
    Retorna o caminho do arquivo de log
    """
    if os.path.exists("/var/log"):
        log_dir = Path("/var/log/openmind-ai")
    else:
        log_dir = Path("logs")
    
    log_files = {
        "app": "app.log",
        "error": "errors.log",
        "errors": "errors.log",
        "access": "access.log",
        "analysis": "analysis.log"
    }
    
    filename = log_files.get(log_type.lower(), "app.log")
    return str(log_dir / filename)



