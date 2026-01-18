from abc import ABC, abstractmethod
class BaseIngestor():
    @abstractmethod
    def load(self,source:str)->any:
        pass