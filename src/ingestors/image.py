import logging
import os
import subprocess
import sys
from .base import BaseIngestor
import base64
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

class ImageIngestor(BaseIngestor):
    def __init__(self,model_name="gemini-2.0-flash"):
        self.llm=ChatGoogleGenerativeAI(model=model_name)
    def load(self, source: str) -> str:
        """
        Extracts text from an image using an isolated PaddleOCR process.
        This avoids dependency conflicts between PaddleOCR and LangChain.
        """
        if not os.path.exists(source):
            logger.error(f"Image file not found: {source}")
            return ""

        try:
            from paddleocr import PaddleOCR
            # Initialize PaddleOCR (english, use_angle_cls=False to be safe)
            # We lazy load this because it's heavy
            ocr = PaddleOCR(use_angle_cls=False, lang='en', show_log=False)
            
            logger.info(f"Running direct PaddleOCR on {source}...")
            result = ocr.ocr(source, cls=False)
            
            full_text = []
            if result and result[0]:
                for line in result[0]:
                    text = line[1][0]
                    full_text.append(text)
            
            text = " ".join(full_text)
            
            # If OCR result is too sparse (likely a diagram/chart), use Vision Model
            if len(text) < 50:
                logger.info(f"OCR text length ({len(text)}) below threshold. Falling back to Gemini Vision.")
                return self._analyze_with_gemini(source)
                
            return text

        except Exception as e:
            logger.error(f"OCR failed: {e}")
            # Fallback to Vision Model on error as well
            return self._analyze_with_gemini(source)

    def _analyze_with_gemini(self,image_path:str)->str:
        try:
            logger.info("Local OCR failed to give enough context switching to LLM")

            with open(image_path,"rb") as image_file:
                image_bytes=image_file.read()
                encoded_bytes=base64.b64encode(image_bytes)
                encoded_string=encoded_bytes.decode("utf-8")

            message = HumanMessage(
                content=[
                    {"type": "text", "text": "This image contains a diagram, chart, or visual content. Please analyze it in detail, extracting any labels, data points, and explaining the visual concepts presented. The goal is to generate quiz questions based on this information."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_string}"}}
                ]
            )

            response=self.llm.invoke([message])
            return response.content
        except Exception as e:
            logger.error(f"Failed to analyze image with LLM: {e}")
            return "Error analyzing the image with the LLM"

    def load_multimodal(self, source: str) -> dict:
        """
        Extracts both text (via OCR/Vision) and the raw image for embedding.
        Returns: {'text_pages': [{'text': str}], 'images': [{'image': PIL.Image, 'id': str}]}
        """
        from PIL import Image
        
        # 1. Get Text (OCR or Vision Description)
        text = self.load(source)
        
        # 2. Get Image Object
        try:
            pil_image = Image.open(source).convert("RGB")
            image_id = os.path.basename(source)
            
            return {
                "text_pages": [{"text": text, "page": 0}],
                "images": [{
                    "image": pil_image,
                    "page": 0,
                    "id": image_id
                }]
            }
        except Exception as e:
            logger.error(f"Failed to load image for multimodal: {e}")
            return {"text_pages": [], "images": []}



