import logging
import os
from pypdf import PdfReader
from .base import BaseIngestor

logger = logging.getLogger(__name__)

class FileIngestor(BaseIngestor):
    def load(self, source: str) -> str:
        """
        Extracts text from a document file.
        Supports: .pdf, .txt, .md, .py, .json, .csv
        """
        logger.info(f"Ingesting document: {source}")
        
        if not os.path.exists(source):
            logger.error(f"File not found: {source}")
            return ""

        ext = os.path.splitext(source)[1].lower()

        try:
            if ext == ".pdf":
                # Fallback to direct PyPDF if Langchain is overkill, or keep using PyPDFReader direct
                # The previous file.py used LangChain but this implementation is lighter
                return self._read_pdf(source)
            elif ext in [".txt", ".md", ".py", ".json", ".csv"]:
                return self._read_text(source)
            else:
                logger.warning(f"Unsupported file extension: {ext}")
                return ""
        except Exception as e:
            logger.error(f"Error reading document {source}: {e}")
            return f"Error reading file: {str(e)}"

    def _read_pdf(self, path: str) -> str:
        text = ""
        try:
            reader = PdfReader(path)
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Failed to parse PDF: {e}")
            raise e

    def _read_text(self, path: str) -> str:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
