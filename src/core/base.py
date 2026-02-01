"""
Base Downloader Module
Contains abstract base class and common utilities for all downloaders.
"""

from abc import ABC, abstractmethod
from typing import Callable


class DownloaderBase(ABC):
    """Abstract base class for all video downloaders."""

    # Common HTTP headers for all downloaders
    DEFAULT_HTTP_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Common yt-dlp settings
    DEFAULT_YDL_OPTIONS = {
        "ignoreerrors": True,
        "no_warnings": False,
        "quiet": False,
        "nocheckcertificate": True,
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 30,
        "extractor_args": {
            "youtube": {
                "player_client": ["mweb", "ios", "web"],
            }
        },
    }

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def download(
        self,
        url: str,
        progress_hooks: list[Callable] | None = None,
        skip_duplicate_check: bool = False
    ) -> tuple[bool, str]:
        """
        Download content from the given URL.

        Args:
            url: The URL to download from
            progress_hooks: Optional list of progress callback functions
            skip_duplicate_check: Skip duplicate URL check

        Returns:
            Tuple of (success, message)
        """
        ...

    def get_base_options(self) -> dict:
        """Get base yt-dlp options that can be extended by subclasses."""
        options = self.DEFAULT_YDL_OPTIONS.copy()
        options["http_headers"] = self.DEFAULT_HTTP_HEADERS.copy()
        return options
