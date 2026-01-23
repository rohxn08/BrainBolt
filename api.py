
import os
import shutil
import logging
import time
import uuid
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv


load_dotenv()

# Import existing logic
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.processors.summarizer import SummarizerProcessor
from src.processors.quiz_generator import QuizProcessor
from src.ingestors.search import SearchIngestor
import src.utils as utils # For list_available_models

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
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
    model_name: Optional[str] = "gemini-2.5-flash"
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
    """
    try:
        os.environ["GOOGLE_API_KEY"] = request.api_key
        global summarizer, quiz_generator
        summarizer = SummarizerProcessor(model_name=request.model_name)
        quiz_generator = QuizProcessor(model_name=request.model_name)
        
        # Use utils.list_available_models directly if imported as module, 
        # or call functional logic if available.
        # Assuming list_available_models is in src/utils/__init__.py or similar
        try:
            available_models = utils.list_available_models(request.api_key)
        except AttributeError:
             # Fallback if function is not directly exposed in utils package
             from src.utils import list_available_models
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
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
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
        
        if os.path.exists(source_path):
            # It is a local file
            if ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                from src.ingestors.image import ImageIngestor
                ingestor = ImageIngestor(model_name=request.model_name) 
            else:
                ingestor = FileIngestor()
        
        elif source_path.startswith("http"):
            # It is a URL
            if "youtube.com" in source_path or "youtu.be" in source_path:
                from src.ingestors.youtube import YouTubeIngestor
                ingestor = YouTubeIngestor()
            else:
                ingestor = SearchIngestor()
        
        else:
            # It is a search query or raw text
            ingestor = SearchIngestor()
            
        data = ingestor.load_multimodal(source_path)
        
        if not data or (not data.get("text_pages") and not data.get("images")):
             raise HTTPException(status_code=400, detail="Could not extract content from source")

        # 2. Initialize RAG Processor with selected model
        rag_processor = MultiModalRAGProcessor(model_name=request.model_name)
        ingest_status = rag_processor.ingest_data(data)
        logger.info(f"RAG Ingestion Status: {ingest_status}")

        # 3. Route to Processor
        if request.mode == "summarize":
            current_summarizer = SummarizerProcessor(model_name=request.model_name)
            result = current_summarizer.summarize(
                rag_processor=rag_processor,
                summary_type=request.summary_type
            )
            return {"result": result}
        
        elif request.mode == "quiz":
            current_quiz_generator = QuizProcessor(model_name=request.model_name)
            questions = current_quiz_generator.generate_quiz(
                rag_processor=rag_processor,
                num_questions=request.num_questions,
                difficulty=request.difficulty
            )
            return {"result": questions}
        
        else:
            raise HTTPException(status_code=400, detail="Invalid mode")

    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
