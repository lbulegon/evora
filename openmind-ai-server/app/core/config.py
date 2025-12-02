"""
Configurações do OpenMind AI Server
"""
import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # API - Autenticação do servidor (usada também como fallback para OpenMind.org)
    OPENMIND_AI_API_KEY: str
    OPENMIND_AI_HOST: str = "0.0.0.0"
    OPENMIND_AI_PORT: int = 8000
    
    # OpenMind.org - LLM principal (você já pagou por isso!)
    # Se não configurado, usa OPENMIND_AI_API_KEY como fallback
    OPENMIND_ORG_API_KEY: str = ""
    OPENMIND_ORG_BASE_URL: str = "https://api.openmind.org/api/core/openai"
    OPENMIND_ORG_MODEL: str = "qwen2.5-vl-72b-instruct"  # Padrão Railway
    
    # IA Backend (fallback)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    
    # Ollama (opcional)
    OLLAMA_BASE_URL: str = ""
    OLLAMA_MODEL: str = "llama3.2-vision"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Image Processing
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_IMAGE_FORMATS: str = "jpeg,jpg,png,webp"
    IMAGE_MAX_DIMENSION: int = 2048
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "/var/log/openmind-ai/server.log"
    
    # CORS
    CORS_ORIGINS: str = "*"
    
    # Security
    TOKEN_EXPIRATION: int = 86400
    
    @property
    def allowed_formats_list(self) -> List[str]:
        """Lista de formatos permitidos"""
        return [fmt.strip().lower() for fmt in self.ALLOWED_IMAGE_FORMATS.split(",")]
    
    @property
    def max_image_size_bytes(self) -> int:
        """Tamanho máximo da imagem em bytes"""
        return self.MAX_IMAGE_SIZE_MB * 1024 * 1024
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Lista de origens CORS"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Instância global de configurações
settings = Settings()
