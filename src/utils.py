import google.generativeai as genai
import os
import logging

logger = logging.getLogger(__name__)

def list_available_models(api_key: str = None):
    """
    Connects to Google API and lists models that support content generation.
    Returns:
        list: A list of model names (e.g. ['models/gemini-1.5-flash', ...])
        or an empty list if failed.
    """
    
    # 1. Configure the API with the provided key (or env var)
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        logger.error("No API Key provided.")
        return []

    try:
        genai.configure(api_key=api_key)
        
        # 2. Ask Google for all available models
        all_models = genai.list_models()
        
        # 3. Filter only the ones that can 'generateContent' (chat models)
        chat_models = []
        for m in all_models:
            if 'generateContent' in m.supported_generation_methods:
                # We strip 'models/' prefix for cleaner UI (optional)
                clean_name = m.name.replace("models/", "") 
                chat_models.append(clean_name)
                
        logger.info(f"Retrieved {len(chat_models)} models.")
        return chat_models

    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        return []

if __name__ == "__main__":
    # Test block to run this file directly
    from dotenv import load_dotenv
    load_dotenv()
    print("Available Models:", list_available_models())