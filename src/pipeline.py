import logging
import os
from .ingestors.image import ImageIngestor
from .ingestors.youtube import YouTubeIngestor
from .processors.summarizer import SummarizerProcessor


logger=logging.getLogger(__name__)

class BrainBoltPipeline:
    def __init__(self):
        self.image_ingestor=ImageIngestor()
        self.youtube_ingestor=YouTubeIngestor()
        self.summarizer=SummarizerProcessor()

    def process(self,source:str, task:str="summarize", **kwargs):
        logger.info(f"Prcoessing {source} for {task}")
        content_text=self._ingest(source)
        if not content_text:
            return {"error":"Failed to ingest the content and to extract"}
        if task=="summarize":
            summary_type=kwargs.get("summary_type","concise")
            result=self.summarizer.summarize(content_text,summary_type=summary_type)

            return {"result":result,
            "source_text_length":len(content_text)}
        else:
            return {"error": f"Unsupported task:{task}"}
        
    def _ingest(self,source:str)->str:
        if "youtube.com" in source or "youtu.be" in source:
            return self.youtube_ingestor.load(source)
        elif source.lower().endswith((".jpg",".jpeg",".png",".webp",".svg",".bmp")):
            return self.image_ingestor.load(source)
        else:
            logger.warning(f"No specific ingestor found for {source}.Treating as raw file/text path")

            if os.path.exists(source):
                try:
                    with open(source,"r",encoding="utf-8") as f:
                        return f.read()
                except Exception as e:
                    logger.error(f"Failed to read file {source}: {str(e)}")
                    return ""
        return source
            