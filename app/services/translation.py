import httpx
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def translate_text(text: str, target_lang: str = "es", source_lang: str = "en") -> str:
    """
    Translate text using DeepL API.
    Falls back to original text if API key is not configured or on error.
    """
    if not text or not text.strip():
        return text
    
    # Check if API key is configured
    if not settings.DEEPL_API_KEY:
        logger.warning("DeepL API key not configured, returning original text")
        return text
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api-free.deepl.com/v2/translate",
                data={
                    "auth_key": settings.DEEPL_API_KEY,
                    "text": text,
                    "target_lang": target_lang.upper(),
                    "source_lang": source_lang.upper(),
                    "tag_handling": "html",  # Preserve HTML tags in instructions
                }
            )
            response.raise_for_status()
            result = response.json()
            
            translated = result["translations"][0]["text"]
            logger.info(f"Translated: '{text[:50]}...' -> '{translated[:50]}...'")
            return translated
            
    except httpx.HTTPStatusError as e:
        logger.error(f"DeepL API error: {e.response.status_code} - {e.response.text}")
        return text  # Fallback to original
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return text  # Fallback to original

