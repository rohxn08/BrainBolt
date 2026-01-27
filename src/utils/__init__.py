
import os
import shutil
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def list_available_models(api_key: str) -> List[str]:
    """
    Lists available Gemini models using the provided API key.
    Filters for strictly 'gemini-pro' and 'gemini-1.5' variants suitable for chat.
    """
    import google.generativeai as genai
    
    try:
        genai.configure(api_key=api_key)
        models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini' in m.name:
                    # Clean up the name (models/gemini-pro -> gemini-pro)
                    clean_name = m.name.replace('models/', '')
                    models.append(clean_name)
        return models
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        # Fallback list if API call fails
        return ["gemini-pro", "gemini-1.5-flash", "gemini-1.5-pro-latest"]
