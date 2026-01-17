import os
import shutil
import logging
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Import existing logic
# Assuming src is in the python path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.processors.summarizer import SummarizerProcessor
from src.processors.quiz_generator import QuizProcessor
from src.ingestors.search import SearchIngestor
from src.utils import list_available_models
# (Add other ingestors as needed, e.g. PDF/Image if you have them,
# or simply treat 'source_path' as text for now if it's a raw file path)

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development convenience
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (lazy loaded or initialized via /api/init)
# Global instances (lazy loaded or initialized via /api/init)
summarizer = None
quiz_generator = None

# -----------------
# DATA MODELS
# -----------------
class InitRequest(BaseModel):
    api_key: str
    model_name: str = "gemini-2.0-flash"

class ProcessRequest(BaseModel):
    source_path: str
    mode: str  # "summarize" or "quiz"
    # Summarizer specific
    summary_type: Optional[str] = "concise"
    # Quiz specific
    num_questions: Optional[int] = 5
    difficulty: Optional[str] = "Medium"

# -----------------
# UTILS
# -----------------
TEMP_DIR = os.path.join(os.getcwd(), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

def read_file_content(file_path: str) -> str:
    """
    Simple helper to read text from uploaded file.
    For a real 'Universal Ingestor', this would use your `src.ingestors` logic
    to parse PDF, Images, etc.
    """
    try:
        # Detect if it's a URL (for simplicity in this demo, though frontend handles distinction)
        if file_path.startswith("http"):
            # Use SearchIngestor or similar for URLs
            ingestor = SearchIngestor()
            return ingestor.load(file_path) # Treating URL as query/link

        # If local file
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading source: {e}")
        return ""

# -----------------
# API ENDPOINTS
# -----------------

@app.post("/api/init")
async def init_session(request: InitRequest):
    """
    Initialize session with API Key.
    In a real multi-user app, this would use sessions/cookies.
    """
    try:
        os.environ["GOOGLE_API_KEY"] = request.api_key
        # Re-initialize processors with new key if needed
        # (LangChain usually picks up env var automatically on instantiation,
        # but re-instantiating ensures it)
        global summarizer, quiz_generator
        summarizer = SummarizerProcessor(model_name=request.model_name)
        quiz_generator = QuizProcessor(model_name=request.model_name)
        
        # Get actual available models
        available_models = list_available_models(request.api_key)
        
        return {
            "status": "success", 
            "message": "System initialized",
            "models": available_models
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Handle file uploads.
    """
    try:
        file_location = os.path.join(TEMP_DIR, file.filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File saved to {file_location}")
        return {"file_path": file_location, "filename": file.filename}
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")

@app.post("/api/process")
async def process_content(request: ProcessRequest):
    """
    Main processing endpoint for Summarization and Quiz.
    """
    try:
        # 1. Extract Content
        # In a robust app, you'd use your specific Ingestor classes here based on file extension
        text_content = read_file_content(request.source_path)
        
        if not text_content:
            raise HTTPException(status_code=400, detail="Could not extract text from source")

        # 2. Route to Processor
        if request.mode == "summarize":
            if not summarizer:
                raise HTTPException(status_code=500, detail="Summarizer not initialized")
            
            result = summarizer.summarize(
                text=text_content,
                summary_type=request.summary_type
            )
            return {"result": result}

        elif request.mode == "quiz":
            if not quiz_generator:
                raise HTTPException(status_code=500, detail="Quiz Generator not initialized")
            
            questions = quiz_generator.generate_quiz(
                text=text_content,
                num_questions=request.num_questions,
                difficulty=request.difficulty
            )
            return {"result": questions}
        
        else:
            raise HTTPException(status_code=400, detail="Invalid mode")

    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------
# STATIC MOUNT
# -----------------
# Mount the frontend directory to serve HTML/CSS/JS
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Allow running directly: python api.py
    uvicorn.run(app, host="0.0.0.0", port=8000)
