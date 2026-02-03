"""
Base Controller Module
Defines the base class for all UI controllers.
"""

from abc import ABC, abstractmethod
from typing import Any
from src.utils.logger import get_logger


class BaseController(ABC):
    """Abstract base class for controllers."""

    def __init__(self, config: Any, ui: Any):
        """
        Initialize controller with shared resources.
        
        Args:
            config: Config instance
            ui: Interface instance
        """
        self.config = config
        self.ui = ui
        self.logger = get_logger()

    @abstractmethod
    def run(self) -> None:
        """Main loop for the controller."""
        pass

    def handle_error(self, e: Exception, context: str) -> None:
        """Centralized error handling for controllers."""
        self.logger.exception(f"Error in {context}", exc=e)
        self.ui.show_error(f"{context} sırasında bir hata oluştu:\n{e}")
        self.ui.wait_for_enter()
