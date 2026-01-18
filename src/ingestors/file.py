import logging
import os

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
        # Replaced pypdf with fitz
        import fitz
        text = ""
        try:
            doc = fitz.open(path)
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            return text
        except Exception as e:
            logger.error(f"Failed to parse PDF: {e}")
            raise e

    def _read_text(self, path: str) -> str:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def load_multimodal(self, source: str) -> dict:
        """
        Extracts both text and images from a document.
        Returns: {'text_pages': [{'text': str, 'page': int}], 'images': [{'image': PIL.Image, 'page': int, 'id': str}]}
        """
        if not os.path.exists(source):
            return {"text_pages": [], "images": []}
            
        ext = os.path.splitext(source)[1].lower()
        if ext == ".pdf":
            return self._read_pdf_multimodal(source)
        else:
            # Fallback for text-only files
            text = self.load(source)
            return {
                "text_pages": [{"text": text, "page": 0}], 
                "images": []
            }

    def _read_pdf_multimodal(self, path: str) -> dict:
        import fitz
        from PIL import Image
        import io
        
        doc = fitz.open(path)
        result = {"text_pages": [], "images": []}
        
        for i, page in enumerate(doc):
            # Extract Text
            text = page.get_text()
            if text.strip():
                result["text_pages"].append({"text": text, "page": i})
            
            # Extract Images
            for img_index, img in enumerate(page.get_images(full=True)):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                    image_id = f"page{i}_img{img_index}"
                    
                    result["images"].append({
                        "image": pil_image,
                        "page": i,
                        "id": image_id
                    })
                except Exception as e:
                    logger.warning(f"Error extracting image {img_index} on page {i}: {e}")
        
        doc.close()
        return result
