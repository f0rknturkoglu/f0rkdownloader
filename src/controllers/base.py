"""
Base Controller Module
Defines the base class for all UI controllers.
"""

import sys
from abc import ABC, abstractmethod
from pathlib import Path
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

    @staticmethod
    def get_resource_path(relative_path: str) -> Path:
        """
        Get absolute path to resource, works for dev and for PyInstaller bundle.
        """
        if hasattr(sys, "_MEIPASS"):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).resolve().parent.parent.parent
        return base_path / relative_path

    def handle_error(self, e: Exception, context: str) -> None:
        """Centralized error handling for controllers."""
        self.logger.exception(f"Error in {context}", exc=e)
        self.ui.show_error(f"{context} sırasında bir hata oluştu:\n{e}")
        self.ui.wait_for_enter()
