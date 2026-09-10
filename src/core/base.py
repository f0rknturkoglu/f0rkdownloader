"""
Base Downloader Module
Defines the base class and core utilities for all downloaders.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

# ==================== Custom Exceptions ====================

class DownloaderError(Exception):
    """Base exception for all downloader errors."""

class AuthenticationError(DownloaderError):
    """Raised when authentication fails."""

class DownloadError(DownloaderError):
    """Raised when download process fails."""

class NetworkError(DownloaderError):
    """Raised when network issues occur."""

class ValidationError(DownloaderError):
    """Raised when input validation fails."""


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

    def get_base_options(self) -> dict[str, Any]:
        """Get common yt-dlp options based on config."""
        is_audio = self.config.format_type == "audio"
        opts: dict[str, Any] = {
            "format": "bestaudio/best" if is_audio else self.config.quality,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "socket_timeout": 30,
            "retries": 5,
            "file_access_retries": 3,
            "js_runtimes": {
                "node": {},
                "deno": {},
                "bun": {},
                "quickjs": {},
            },
        }

        if is_audio:
            opts["writethumbnail"] = True
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                },
                {
                    "key": "FFmpegMetadata",
                    "add_metadata": True,
                },
                {
                    "key": "EmbedThumbnail",
                    "already_have_thumbnail": False,
                },
            ]
        else:
            opts["merge_output_format"] = "mp4"
            opts["postprocessors"] = [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4",
                }
            ]

        return opts

    @staticmethod
    def find_executable(name: str) -> str | None:
        """
        Locate executable in system PATH, active virtualenv, or python script folders.
        """
        import shutil
        import sys
        from pathlib import Path

        found = shutil.which(name)
        if found:
            return found

        candidates = [
            Path(sys.prefix) / "Scripts" / f"{name}.exe",
            Path(sys.prefix) / "Scripts" / name,
            Path(sys.prefix) / "bin" / name,
            Path(sys.executable).parent / f"{name}.exe",
            Path(sys.executable).parent / name,
        ]
        for c in candidates:
            if c.is_file():
                return str(c)
        return None

