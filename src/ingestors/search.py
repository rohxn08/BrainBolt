from .base import BaseIngestor
import logging
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.utilities  import DuckDuckGoSearchAPIWrapper

logger=logging.getLogger(__name__)
class SearchIngestor(BaseIngestor):
    def __init__(self,num_results=3):
        self.num_results=num_results
        self.wrapper=DuckDuckGoSearchAPIWrapper(max_results=num_results)
        

    #Loading method 

    def load(self,query:str)->str:
        logger.info(f"Searching the WEB for {query}")
        search_results=self.wrapper.results(query,max_results=self.num_results)
        urls=[res['link'] for res in search_results]

        if not urls:
            return f"No results found on the web for {query}"

        logger.info(f"Found{urls} for {query}")

        try:
            loader=WebBaseLoader(urls,header_template={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
            docs=loader.load()
            full_text="\n".join([d.page_content for d in docs])
            return full_text
        except Exception as e:
            logger.error(f"Error in loading the web content Please check the URL{e}")
            return str(e)

    def load_multimodal(self, query: str) -> dict:
        """
        Performs web search and returns scraped content as distinct pages.
        """
        logger.info(f"Multimodal Web Search: {query}")
        
        try:
        
            # 1. Get URLs (Smart Detection: Direct Link vs Search Query)
            urls = []
            if query.startswith("http://") or query.startswith("https://"):
                logger.info("Direct Link functionality detected. Skipping Search.")
                urls = [query]
            else:
                search_results = self.wrapper.results(query, max_results=self.num_results)
                urls = [res['link'] for res in search_results]
            
            if not urls:
                return {"text_pages": [], "images": []}

            # 2. Load and Clean Content per URL
            result_pages = []
            
            # We load individually to keep them separate in RAG context
            for i, url in enumerate(urls):
                try:
                    loader = WebBaseLoader([url], header_template={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    })
                    
                    # Intercept the scrape to clean it before getting text
                    docs = loader.load()
                    
                    # IMPROVED CLEANING LOGIC using BeautifulSoup attached to the loader
                    # (WebBaseLoader uses BS4 under the hood, but often returns everything.
                    # We can re-parse the page_content if it's raw HTML, but usually it returns text.
                    # Best approach: Use requests + BS4 directly or refining the loader's output is limited.
                    # Let's simple-clean the text or re-fetch for better control.
                    # Given we have the docs, let's try to clean the extracted text or use a better parser.)
                    
                    # PROPOSED FIX: Custom scraping for high quality text
                    import requests
                    from bs4 import BeautifulSoup
                    
                    resp = requests.get(url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' 
                                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }, timeout=10)
                    
                    soup = BeautifulSoup(resp.content, 'html.parser')
                    
                    # 1. Remove Clutter
                    for tag in soup(['nav', 'header', 'footer', 'aside', 'script', 'style', 'noscript', 'form', 'iframe']):
                        tag.decompose()
                        
                    # 2. Focus on Main Content (Heuristic)
                    main_content = soup.find('main') or soup.find('article') or soup.find(id='content') or soup.find(class_='content') or soup.body
                    
                    if main_content:
                        text = main_content.get_text(separator='\n', strip=True)
                    else:
                        text = soup.get_text(separator='\n', strip=True)

                    
                    if text.strip():
                        # Append URL to text for reference
                        content_with_source = f"Source: {url}\n\n{text}"
                        result_pages.append({"text": content_with_source, "page": i})
                        
                except Exception as e:
                    logger.warning(f"Failed to scrape {url}: {e}")
                    continue

            return {
                "text_pages": result_pages,
                "images": []
            }
            
        except Exception as e:
            logger.error(f"Search multimodal failed: {e}")
            return {"text_pages": [], "images": []} 