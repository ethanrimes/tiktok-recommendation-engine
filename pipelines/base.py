"""Base pipeline class."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
from datetime import datetime

from database.client import SupabaseClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BasePipeline(ABC):
    """Base class for all pipelines."""
    
    def __init__(self, name: str = "pipeline"):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.db_client = SupabaseClient()
        self.start_time = None
        self.metadata = {}
    
    def log(self, message: str, level: str = "info"):
        """Log a message."""
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(f"[{self.name}] {message}")
    
    def start(self):
        """Start the pipeline."""
        self.start_time = datetime.now()
        self.log(f"Starting pipeline at {self.start_time}")
    
    def end(self):
        """End the pipeline."""
        if self.start_time:
            duration = datetime.now() - self.start_time
            self.log(f"Pipeline completed in {duration.total_seconds():.2f} seconds")
    
    @abstractmethod
    def run(self, **kwargs) -> Any:
        """Run the pipeline."""
        pass
    
    def validate_input(self, **kwargs) -> bool:
        """Validate pipeline input."""
        return True
    
    def save_result(self, result: Any, key: str):
        """Save result to database."""
        try:
            self.db_client.save_result(
                pipeline=self.name,
                key=key,
                data=result,
                metadata=self.metadata
            )
            self.log(f"Saved result with key: {key}")
        except Exception as e:
            self.log(f"Failed to save result: {e}", "error")
    
    def load_result(self, key: str) -> Optional[Any]:
        """Load result from database."""
        try:
            result = self.db_client.load_result(
                pipeline=self.name,
                key=key
            )
            if result:
                self.log(f"Loaded result with key: {key}")
            return result
        except Exception as e:
            self.log(f"Failed to load result: {e}", "error")
            return None