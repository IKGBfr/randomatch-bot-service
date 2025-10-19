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
    
    # Bot IDs
    BOT_CAMILLE_ID = os.getenv("BOT_CAMILLE_ID")
    BOT_PAUL_ID = os.getenv("BOT_PAUL_ID")
    
    # Test user ID
    TEST_USER_ID = os.getenv("TEST_USER_ID", "eb2d9d5c-4f9a-4785-a203-1916e72028f2")
    
    # Mode test
    TEST_MODE = os.getenv("TEST_MODE", "true").lower() == "true"
    
    # Initiation settings
    INITIATION_PROBABILITY = 1.0 if TEST_MODE else 0.5
    MIN_DELAY_MINUTES = 0 if TEST_MODE else 15
    MAX_DELAY_MINUTES = 1 if TEST_MODE else 360
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    # Alias snake_case pour compatibilité
    @property
    def bot_camille_id(self):
        return self.BOT_CAMILLE_ID
    
    @property
    def bot_paul_id(self):
        return self.BOT_PAUL_ID
    
    @property
    def test_user_id(self):
        return self.TEST_USER_ID
    
    @property
    def test_mode(self):
        return self.TEST_MODE
    
    @property
    def supabase_url(self):
        return self.SUPABASE_URL
    
    @property
    def supabase_service_key(self):
        return self.SUPABASE_SERVICE_KEY
    
    @property
    def postgres_connection_string(self):
        return self.POSTGRES_CONNECTION_STRING
    
    @property
    def redis_url(self):
        return self.REDIS_URL
    
    @property
    def log_level(self):
        return self.LOG_LEVEL
    
    @property
    def openrouter_api_key(self):
        return self.OPENROUTER_API_KEY
    
    @property
    def openrouter_base_url(self):
        return self.OPENROUTER_BASE_URL
    
    @property
    def openrouter_model(self):
        return self.OPENROUTER_MODEL


# Instance globale
settings = Config()
