"""Client OpenRouter pour génération de messages bot."""
import logging
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)

class OpenRouterClient:
    """Client pour appeler OpenRouter/Grok"""
    
    def __init__(self):
        self.client = OpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY,
            default_headers={
                "HTTP-Referer": settings.OPENROUTER_SITE_URL,
                "X-Title": settings.OPENROUTER_APP_NAME,
            }
        )
        logger.info("✅ OpenRouter client initialisé")
    
    def generate(
        self,
        messages: list,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None
    ):
        """Génère une réponse avec Grok"""
        try:
            response = self.client.chat.completions.create(
                model=model or settings.OPENROUTER_MODEL,
                messages=messages,
                temperature=temperature or settings.DEFAULT_TEMPERATURE,
                max_tokens=max_tokens or settings.MAX_TOKENS,
            )
            
            return {
                'content': response.choices[0].message.content,
                'model': response.model,
                'tokens': {
                    'input': response.usage.prompt_tokens,
                    'output': response.usage.completion_tokens,
                    'total': response.usage.total_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur génération OpenRouter: {e}")
            raise
