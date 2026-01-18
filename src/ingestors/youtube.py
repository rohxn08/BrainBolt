from .base import BaseIngestor
import logging
import re
from langchain_community.document_loaders import YoutubeLoader

logger = logging.getLogger(__name__)

class YouTubeIngestor(BaseIngestor):
    def load(self, source: str) -> str:
        if self._is_url(source):
            logger.info("Fetching YouTube transcript...")
            return self._fetch_transcript(source)
        else:
            logger.info("Using provided raw transcript text.")
            return source

    def _is_url(self, text: str) -> bool:
        return "youtube.com" in text or "youtu.be" in text

    def _fetch_transcript(self, url: str) -> str:
        try:

            loader = YoutubeLoader.from_youtube_url(
                url, 
                add_video_info=True, 
                language=["en", "hi"], 
                translation="en"
            )
            docs = loader.load()
            return "\n".join([d.page_content for d in docs])
        except Exception as e:
            return f"Error fetching transcript: {str(e)}"

    def load_multimodal(self, source: str) -> dict:
        """
        Fetches transcript and returns it in standardized multimodal format.
        """
        transcript = self.load(source)
        # Check if the load() returned an error message
        if transcript.startswith("Error"):
            logger.error(f"Multimodal load failed: {transcript}")
            return {"text_pages": [], "images": []}
            
        return {
            "text_pages": [{"text": transcript, "page": 0}],
            "images": []
        }