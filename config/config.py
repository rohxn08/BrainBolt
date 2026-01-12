import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    PDFS_DIR = os.path.join(DATA_DIR, "pdfs")
    QUESTIONS_FILE = os.path.join(DATA_DIR, "questions.json")

    @staticmethod
    def validate():
        if not Config.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not set in environment variables.")

# Optional: Auto-validate on import or let main do it
# Config.validate()
