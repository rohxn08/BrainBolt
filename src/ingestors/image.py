import logging
import os
import subprocess
import sys
from .base import BaseIngestor

logger = logging.getLogger(__name__)

class ImageIngestor(BaseIngestor):
    def load(self, source: str) -> str:
        """
        Extracts text from an image using an isolated PaddleOCR process.
        This avoids dependency conflicts between PaddleOCR and LangChain.
        """
        if not os.path.exists(source):
            logger.error(f"Image file not found: {source}")
            return ""

        # Determine path to the isolated environment's Python
        # Assumption: The .venv_ocr is in the project root
        project_root = os.getcwd() # or traverse up if needed
        isolated_python = os.path.join(project_root, ".venv_ocr", "Scripts", "python.exe")
        
        # Determine path to the tool script
        script_path = os.path.join(project_root, "src", "tools", "ocr_isolated.py")

        if not os.path.exists(isolated_python):
             # Fallback if venv not found (e.g. in some deployment), try system python or error
             logger.error("Isolated OCR environment not found at .venv_ocr")
             return "Error: OCR environment missing."

        try:
            logger.info(f"Running OCR on {source}...")
            process = subprocess.run(
                [isolated_python, script_path, source],
                capture_output=True,
                text=True,
                check=True
            )
            return process.stdout.strip()

        except subprocess.CalledProcessError as e:
            logger.error(f"OCR failed: {e.stderr}")
            return f"Error extracting text: {e.stderr}"
        except Exception as e:
            logger.error(f"Unexpected error in OCR ingestor: {e}")
            return ""
