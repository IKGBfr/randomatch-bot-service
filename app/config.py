"""Configuration centrale pour le bot service."""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration du bot service"""
    
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    POSTGRES_CONNECTION_STRING = os.getenv("POSTGRES_CONNECTION_STRING")
    
    # Redis (Upstash)
    REDIS_URL = os.getenv("REDIS_URL")
    
    # OpenRouter / Grok
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "x-ai/grok-4-fast")
    OPENROUTER_FALLBACK_MODEL = os.getenv(
        "OPENROUTER_FALLBACK_MODEL",
        "deepseek/deepseek-chat-v3-0324"
    )
    OPENROUTER_BASE_URL = os.getenv(
        "OPENROUTER_BASE_URL",
        "https://openrouter.ai/api/v1"
    )
    OPENROUTER_SITE_URL = os.getenv(
        "OPENROUTER_SITE_URL",
        "https://randomatch.fr"
    )
    OPENROUTER_APP_NAME = os.getenv(
        "OPENROUTER_APP_NAME",
        "RandoMatch"
    )
    
    # Paramètres génération
    DEFAULT_TEMPERATURE = 0.8
    MAX_TOKENS = 200
    
    # Bot IDs (à récupérer depuis Supabase)
    BOT_CAMILLE_ID = os.getenv("BOT_CAMILLE_ID")
    BOT_PAUL_ID = os.getenv("BOT_PAUL_ID")
    
    # Test user ID
    TEST_USER_ID = os.getenv("TEST_USER_ID", "eb2d9d5c-4f9a-4785-a203-1916e72028f2")
    
    # Mode test
    TEST_MODE = os.getenv("TEST_MODE", "true").lower() == "true"
    
    # Initiation settings
    INITIATION_PROBABILITY = float(os.getenv("INITIATION_PROBABILITY", "0.5"))
    MIN_DELAY_MINUTES = int(os.getenv("MIN_DELAY_MINUTES", "15"))
    MAX_DELAY_MINUTES = int(os.getenv("MAX_DELAY_MINUTES", "360"))
    
    # En mode test : délai immédiat
    if TEST_MODE:
        MIN_DELAY_MINUTES = 0
        MAX_DELAY_MINUTES = 1
        INITIATION_PROBABILITY = 1.0  # 100% d'initiation en test
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Instance globale pour compatibilité avec ancien code
settings = Config()
