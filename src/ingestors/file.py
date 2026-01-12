from .base import BaseIngestor
import logging
import os
from langchain_community.document_loaders import PyPDFLoader

logger=logging.getLogger(__name__)

class FileIngestor(BaseIngestor):
    def load(self,source :str)->str:
        logger.info(f"Loading Pdf from the source:{source}")

        if not os.path.exists(source):
            return f"No such file exists at {source}"

        try:
            loader=PyPDFLoader(source)
            pages=loader.load()
            full_text="\n".join([page.page_content for page in pages])
            return full_text
        except Exception as e:
            logger.error(f"Error in loading the PDF:{e}")
            return f"Error in loading the given PDF {str(e)}"
