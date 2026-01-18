from .base import BaseIngestor
import logging
from youtube_transcript_api import YouTubeTranscriptApi

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
            if "v=" in url:
                video_id = url.split("v=")[1].split("&")[0]
            else:
                video_id = url.split("/")[-1]
                
            logger.info(f"Fetching transcript for Video ID: {video_id}")
            
            yt_api = YouTubeTranscriptApi()
            
            transcript_list = yt_api.list(video_id)
            
            try:
                 transcript = transcript_list.find_transcript(['en', 'hi']) 
            except:
                 logger.warning("English/Hindi not found, falling back to first available...")
                 transcript = next(iter(transcript_list))
                 
            data = transcript.fetch()
            
            full_text = " ".join([i.text for i in data])
            return full_text

        except Exception as e:
            logger.error(f"Error fetching transcript: {str(e)}")
            return f"Error fetching transcript: {str(e)}"

    def load_multimodal(self, source: str) -> dict:
        """
        Fetches transcript and returns it in standardized multimodal format.
        """
        transcript = self.load(source)
        if transcript.startswith("Error"):
            logger.error(f"Multimodal load failed: {transcript}")
            return {"text_pages": [], "images": []}
            
        return {
            "text_pages": [{"text": transcript, "page": 0}],
            "images": []
        }