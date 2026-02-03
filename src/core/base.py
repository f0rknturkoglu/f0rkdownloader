"""
Base Downloader Module
Defines the base class and core utilities for all downloaders.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable


# ==================== Custom Exceptions ====================

class DownloaderError(Exception):
    """Base exception for all downloader errors."""
    pass

class AuthenticationError(DownloaderError):
    """Raised when authentication fails."""
    pass

class DownloadError(DownloaderError):
    """Raised when download process fails."""
    pass

class NetworkError(DownloaderError):
    """Raised when network issues occur."""
    pass

class ValidationError(DownloaderError):
    """Raised when input validation fails."""
    pass


# ==================== Abstract Base Class ====================

class DownloaderBase(ABC):
    """Abstract base class for all platform downloaders."""

    def __init__(self, config: Any):
        """
        Initialize downloader with configuration.
        
        Args:
            config: Config instance
        """
        self.config = config
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36'
        }

    @abstractmethod
    def download(
        self, 
        url: str, 
        progress_hooks: list[Callable] | None = None
    ) -> tuple[bool, str]:
        """
        Download content from URL.
        
        Args:
            url: Target URL
            progress_hooks: Optional yt-dlp style progress hooks
            
        Returns:
            Tuple of (success_status, message)
        """
        pass

    def get_base_options(self) -> dict[str, Any]:
        """Get common yt-dlp options based on config."""
        return {
            "format": self.config.quality,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "merge_output_format": "mp4",
            "postprocessors": [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4",
                }
            ] if self.config.format_type == "video" else [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }
