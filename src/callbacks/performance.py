
import time
from langchain_core.callbacks import BaseCallbackHandler
from src.utils.metrics import metrics_manager

class PerformanceCallback(BaseCallbackHandler):
    def __init__(self):
        self.start_time = None
        self.first_token_time = None
        self.end_time = None
        self.token_count = 0
        
    def on_llm_start(self, serialized, messages, **kwargs):
        """Called when LLM starts processing."""
        self.start_time = time.perf_counter()
        self.first_token_time = None # Reset
        self.token_count = 0
        
    def on_llm_new_token(self, token: str, **kwargs):
        """Called for every new token generated."""
        if self.first_token_time is None:
            self.first_token_time = time.perf_counter()
        self.token_count += 1
        
    def on_llm_end(self, response, **kwargs):
        """Called when LLM finishes generation."""
        self.end_time = time.perf_counter()
        
        # Calculate final stats and push to global manager
        if self.start_time:
            ttft = (self.first_token_time - self.start_time) if self.first_token_time else 0
            
            # Generation time is strictly (First Token -> End), or (Start -> End) if no tokens (non-streaming failover)
            if self.first_token_time and self.end_time:
                gen_time = self.end_time - self.first_token_time
            elif self.end_time:
                gen_time = self.end_time - self.start_time
            else:
                gen_time = 0
                
            metrics_manager.log_llm_metrics(
                ttft_sec=ttft,
                gen_sec=gen_time,
                tokens=self.token_count
            )
