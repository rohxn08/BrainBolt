from .base import BaseIngestor
import logging

logging=logging.getLogger(__name__)

class ImageIngestor(BaseIngestor):
    def load(self,source:str)->str:
        logger.info(f"processing the image:{source}")

        #TODO paddle ocr and integration with gemini api

        return f"[MOCK OCR] extracted text from the image {source}"