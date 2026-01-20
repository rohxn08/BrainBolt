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
    model_name: str = "gemini-2.5-flash"

class ProcessRequest(BaseModel):
    source_path: str
    mode: str  # "summarize" or "quiz"
    model_name: Optional[str] = "gemini-2.5-flash"  # Added model_name
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
        # Check file size (Read into memory to check size - efficient for small limits like 10MB)
        # Alternatively, seek to end to get size if supported, or read chunks.
        # Simple method for FastAPI UploadFile:
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0) # Reset cursor
        
        MAX_SIZE_MB = 10
        if file_size > MAX_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=413, detail=f"File exceeds maximum size of {MAX_SIZE_MB}MB")

        file_location = os.path.join(TEMP_DIR, file.filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File saved to {file_location} (Size: {file_size/1024/1024:.2f} MB)")
        return {"file_path": file_location, "filename": file.filename}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")

@app.post("/api/process")
async def process_content(request: ProcessRequest):
    """
    Main processing endpoint for Summarization and Quiz.
    Uses MultiModalRAGProcessor for context-aware processing.
    """
    try:
        from src.ingestors.file import FileIngestor
        from src.processors.multimodal_rag import MultiModalRAGProcessor
        
        source_path = request.source_path
        
        # 1. Ingest Data (Text + Images)
        ingestor = None
        ext = os.path.splitext(source_path)[1].lower()
        
        if source_path.startswith("http"):
            if "youtube.com" in source_path or "youtu.be" in source_path:
                from src.ingestors.youtube import YouTubeIngestor
                ingestor = YouTubeIngestor()
            else:
                ingestor = SearchIngestor()
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp']:
            from src.ingestors.image import ImageIngestor
            # Pass model_name to ImageIngestor
            ingestor = ImageIngestor(model_name=request.model_name) 
        else:
            ingestor = FileIngestor()
            
        data = ingestor.load_multimodal(source_path)
        
        if not data or (not data.get("text_pages") and not data.get("images")):
             raise HTTPException(status_code=400, detail="Could not extract content from source")

        # 2. Initialize RAG Processor with selected model
        rag_processor = MultiModalRAGProcessor(model_name=request.model_name)
        ingest_status = rag_processor.ingest_data(data)
        logger.info(f"RAG Ingestion Status: {ingest_status}")

        # 3. Route to Processor
        if request.mode == "summarize":
            # Re-instantiate summarizer to ensure correct model is used per request
            # This avoids race conditions with globals and ensures consistency
            current_summarizer = SummarizerProcessor(model_name=request.model_name)
            
            # Pass the RAG processor to the summarizer
            result = current_summarizer.summarize(
                rag_processor=rag_processor,
                summary_type=request.summary_type
            )
            return {"result": result}

        elif request.mode == "quiz":
            # Re-instantiate quiz generator for consistency
            current_quiz_generator = QuizProcessor(model_name=request.model_name)
            
            # For now, Quiz Generator uses raw text.
            # We reconstruct text from the ingested pages.
            full_text = ""
            for page in data.get("text_pages", []):
                full_text += f"{page.get('text', '')}\n\n"
            
            if not full_text.strip():
                 # Fallback if only images?
                 full_text = "Analysis of the provided images revealed no directly extractable text for quiz generation."

            questions = current_quiz_generator.generate_quiz(
                text=full_text,
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
