from .base import BaseIngestor
import logging
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

logger = logging.getLogger(__name__)

class YouTubeIngestor(BaseIngestor):
    def load(self, source: str) -> str:
        if self._is_youtube_url(source):
            return self._get_transcript_text(source)
        return source

    def load_multimodal(self, url: str) -> dict:
        """
        Extracts transcript from a YouTube video URL.
        """
        if not self._is_youtube_url(url):
             return {"text_pages": [], "images": []}

        try:
            full_text = self._get_transcript_text(url)
            
            if not full_text or (isinstance(full_text, str) and full_text.startswith("Error")):
                 logger.error(f"YouTube Ingestion Failure: {full_text}")
                 return {
                    "text_pages": [{
                        "text": f"System Error: {full_text}", 
                        "page": 0
                    }],
                    "images": []
                }

            return {
                "text_pages": [{
                    "text": f"Video Transcript ({url}):\n\n{full_text}",
                    "page": 0
                }],
                "images": [] 
            }

        except Exception as e:
            logger.error(f"YouTube ingestion failed: {e}")
            return {
                "text_pages": [{
                    "text": f"System Error: {str(e)}", 
                    "page": 0
                }],
                "images": []
            }

    def _is_youtube_url(self, text: str) -> bool:
        return "youtube.com" in text or "youtu.be" in text

    def _get_video_id(self, url: str) -> str:
        if "v=" in url:
            return url.split("v=")[1].split("&")[0]
        else:
            return url.split("/")[-1]

    def _get_transcript_text(self, url: str) -> str:
        try:
            video_id = self._get_video_id(url)
            logger.info(f"Fetching transcript for Video ID: {video_id}")
            
            yt_api = YouTubeTranscriptApi()
            
            try:
                # User's verified code uses .list()
                if hasattr(yt_api, 'list'):
                    transcript_list = yt_api.list(video_id)
                else:
                    # Fallback to standard library usage if .list() doesn't exist
                    transcript_list = yt_api.list_transcripts(video_id)
            except AttributeError:
                 # Fallback for static method usage if instance method fails
                 transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            try:
                 transcript = transcript_list.find_transcript(['en'])
            except:
                 logger.info("English not found, falling back to first available...")
                 transcript = next(iter(transcript_list))
                 
            data = transcript.fetch()
            
            # Handle both object (user code) and dict (standard lib) formats
            try:
                full_text = " ".join([i.text for i in data])
            except AttributeError:
                full_text = " ".join([i['text'] for i in data])
                
            return full_text

        except Exception as e:
            logger.error(f"Error fetching transcript: {e}")
            return f"Error fetching transcript: {str(e)}"