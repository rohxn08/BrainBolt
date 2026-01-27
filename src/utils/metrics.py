
import time
from collections import deque
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class MetricsManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MetricsManager, cls).__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        # Store last 50 requests
        self.history: deque = deque(maxlen=50)
        self.current_trace: Dict[str, Any] = {}
    
    def start_trace(self, trace_id: str, task: str):
        self.current_trace = {
            "id": trace_id,
            "task": task,
            "start_time": time.perf_counter(),
            "retrieval_ms": 0,
            "generation_ms": 0,
            "ttft_ms": 0,
            "total_ms": 0,
            "output_tokens": 0,
            "throughput": 0
        }
        
    def log_retrieval(self, duration_sec: float):
        if self.current_trace:
            self.current_trace["retrieval_ms"] = round(duration_sec * 1000, 2)
            
    def log_llm_metrics(self, ttft_sec: float, gen_sec: float, tokens: int):
        if self.current_trace:
            self.current_trace["ttft_ms"] = round(ttft_sec * 1000, 2)
            self.current_trace["generation_ms"] = round(gen_sec * 1000, 2)
            self.current_trace["output_tokens"] = tokens
            if gen_sec > 0:
                self.current_trace["throughput"] = round(tokens / gen_sec, 2)
                
    def end_trace(self):
        if self.current_trace:
            end_time = time.perf_counter()
            start_time = self.current_trace.get("start_time", end_time)
            self.current_trace["total_ms"] = round((end_time - start_time) * 1000, 2)
            
            # Add to history
            self.history.append(self.current_trace.copy())
            
            # LOG TO TERMINAL FOR ADMIN VISIBILITY
            log_msg = (
                 f"\n[PERFROMANCE METRICS] Task: {self.current_trace.get('task')}\n"
                 f"  - Latency   : {self.current_trace.get('total_ms')} ms\n"
                 f"  - TTFT      : {self.current_trace.get('ttft_ms')} ms\n"
                 f"  - Retrieval : {self.current_trace.get('retrieval_ms')} ms\n"
                 f"  - Throughput: {self.current_trace.get('throughput')} T/s\n"
            )
            print(log_msg) # Print to stdout
            logger.info(f"Trace completed: {self.current_trace}")
            self.current_trace = {} # Reset
            
    def get_latest_metrics(self) -> Dict:
        if len(self.history) > 0:
            return self.history[-1]
        return {}
        
    def get_history(self) -> List[Dict]:
        return list(self.history)

# Global Instance
metrics_manager = MetricsManager()
