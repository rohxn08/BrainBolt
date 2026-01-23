import logging
import os
from .ingestors.image import ImageIngestor
from .ingestors.youtube import YouTubeIngestor
from .processors.summarizer import SummarizerProcessor
from .processors.quiz_generator import QuizProcessor
from .processors.multimodal_rag import MultiModalRAGProcessor

logger = logging.getLogger(__name__)

class BrainBoltPipeline:
    def __init__(self, model_name="gemini-2.5-flash"):
        self.image_ingestor = ImageIngestor(model_name=model_name)
        self.youtube_ingestor = YouTubeIngestor()
        
        # Initialize RAG Processor
        self.rag_processor = MultiModalRAGProcessor(model_name=model_name)
        
        self.summarizer = SummarizerProcessor(model_name=model_name)
        self.quiz_generator = QuizProcessor(model_name=model_name)

    def process(self, source: str, task: str = "summarize", **kwargs):
        logger.info(f"Processing {source} for {task}")
        
        # 1. Ingest into Standardized Dictionary
        data_dict = self._ingest(source)
        
        # Check if ingestion returned valid data
        has_text = bool(data_dict.get("text_pages"))
        has_images = bool(data_dict.get("images"))
        
        if not (has_text or has_images):
             return {"error": "Failed to ingest content or extract data"}

        # 2. Ingest into RAG System
        # Clear previous session data? For a pipeline instance, maybe we want this.
        # But RAG processor usually appends. For now, let's assume one-shot use or it appends.
        # Ideally we might want to clear it if it's a new request, but let's just ingest.
        ingest_status = self.rag_processor.ingest_data(data_dict)
        if "Error" in ingest_status:
            return {"error": f"RAG Ingestion failed: {ingest_status}"}

        # 3. Route to Processor
        if task == "summarize":
            summary_type = kwargs.get("summary_type", "concise")
            result = self.summarizer.summarize(self.rag_processor, summary_type=summary_type)

            source_len = sum(len(p.get("text", "")) for p in data_dict.get("text_pages", []))
            return {
                "result": result,
                "source_text_length": source_len
            }
            
        elif task == "quiz":
            num_q = kwargs.get("num_questions", 5)
            diff = kwargs.get("difficulty", "medium")
            
            # Use RAG processor for quiz generation
            result = self.quiz_generator.generate_quiz(self.rag_processor, num_questions=num_q, difficulty=diff)
            
            source_len = sum(len(p.get("text", "")) for p in data_dict.get("text_pages", []))
            return {
                "result": result,
                "source_text_length": source_len
            }
        else:
            return {"error": "Invalid task"}

    def _ingest(self, source: str) -> dict:
        """
        Ingests content and returns a standardized dictionary:
        {
            "text_pages": [{"text": "...", "page": 0}],
            "images": [{"image": PIL_Image, "id": "...", "page": 0}]
        }
        """
        if "youtube.com" in source or "youtu.be" in source:
            return self.youtube_ingestor.load_multimodal(source)
        
        elif source.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".svg", ".bmp")):
            return self.image_ingestor.load_multimodal(source)
            
        else:
            # Fallback for text files or raw text
            if os.path.exists(source):
                try:
                    with open(source, "r", encoding="utf-8") as f:
                        content = f.read()
                    return {
                        "text_pages": [{"text": content, "page": 0}],
                        "images": []
                    }
                except Exception as e:
                    logger.error(f"Failed to read file {source}: {str(e)}")
                    return {"text_pages": [], "images": []}
            
            # Treat as raw text if it looks like text and isn't a path
            if len(source) > 0 and len(source) < 200000: 
                 return {
                        "text_pages": [{"text": source, "page": 0}],
                        "images": []
                    }

        return {"text_pages": [], "images": []}
