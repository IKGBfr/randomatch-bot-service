"""Configuration module pour RandoMatch Bot Service."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Charger le .env explicitement AVANT tout
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)


class Settings(BaseSettings):
    """Configuration globale du service bot."""
    
    # Supabase
    supabase_url: str
    supabase_service_key: str
    postgres_connection_string: str
    
    # Redis (Upstash)
    redis_url: str
    
    # OpenRouter
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "x-ai/grok-4-fast"
    
    # Bot Configuration (global)
    typing_speed_cps: float = 3.5  # Caractères par seconde
    min_thinking_delay: int = 3  # Secondes
    max_thinking_delay: int = 15  # Secondes
    
    # Environment
    environment: str = "production"
    log_level: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def is_production(self) -> bool:
        """Vérifie si on est en production."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Vérifie si on est en développement."""
        return self.environment.lower() in ("development", "dev")


# Instance globale créée APRÈS le load_dotenv
settings = Settings()


def get_settings() -> Settings:
    """Retourne l'instance des settings."""
    return settings
