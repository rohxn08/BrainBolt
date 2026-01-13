from .base import BaseIngestor
import logging
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.utilities  import DuckDuckGoSearchAPIWrapper

class SearchIngestor(BaseIngestor):
    def __init__(self,num_results=3):
        self.num_results=num_results
        self.wrapper=DuckDuckGoSearchAPIWrapper(max_results=num_results)
        self.tool=DuckDuckGoSearchRun(api_wrapper=self.wrapper)

    #Loading method 

    def load(self,query:str)->str:
        logger.info(f"Searching the WEB for {query}")
        search_results=self.wrapper.results(query,max_results=self.num_results)
        urls=[res['link'] for res in search_results]

        if not urls:
            return f"No results found on the web for {query}"

        logger.info(f"Found{urls} for {query}")

        try:
            loader=WebBaseLoader(urls)
            docs=loader.load()
            full_text="\n".join([d.page_content for d in docs])
            return full_text
        except Exception as e:
            logger.error(f"Error in loading the web content Please check the URL{e}")
            return str(e) 