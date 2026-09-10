"""
Application Configuration
Handles all app settings with JSON persistence.
"""

import json
import os
from pathlib import Path
from typing import Any


class Config:
    """Application configuration management with persistence."""

    # Application info
    APP_NAME = "f0rkn_d0wnl0ader"
    VERSION = "2.1.0"
    
    # Config file name
    CONFIG_FILE = "settings.json"

    def __init__(self):
        # Base download directory
        self.base_download_path = Path(
            os.path.expanduser("~")) / "Downloads" / self.APP_NAME

        # Backwards compatibility - main download path
        self.download_path = str(self.base_download_path)

        # Platform-specific paths
        self.youtube_path = self.base_download_path / "YouTube"
        self.twitter_path = self.base_download_path / "Twitter"
        self.tiktok_path = self.base_download_path / "TikTok"
        self.facebook_path = self.base_download_path / "Facebook"
        self.instagram_path = self.base_download_path / "Instagram"
        self.pinterest_path = self.base_download_path / "Pinterest"

        # Config file path
        self.config_file_path = self.base_download_path / self.CONFIG_FILE

        # Default settings
        self._set_defaults()
        
        # Create directories
        self._create_directories()
        
        # Load saved settings
        self.load()

    def _set_defaults(self) -> None:
        """Set default values for all settings."""
        # YouTube settings
        self.quality: str = "bestvideo+bestaudio/best"
        self.format_type: str = "video"  # video veya audio

        # YouTube Authentication settings
        self.auth_method: str | None = None
        self.browser: str | None = "chrome"
        self.cookies_file: str | None = None
        self.channel_name: str | None = None

        # Twitter/X Authentication settings
        self.twitter_cookies_file: str | None = None
        self.twitter_username: str | None = None

        # TikTok Authentication settings
        self.tiktok_cookies_file: str | None = None
        self.tiktok_username: str | None = None

        # Facebook Authentication
        self.facebook_cookies_file: str | None = None

        # Instagram Authentication
        self.instagram_cookies_file: str | None = None

        # Pinterest Authentication
        self.pinterest_cookies_file: str | None = None

        # Concurrency settings
        self.max_workers: int = 3

        # Theme settings
        self.theme_color: str = "ubuntu"

    def _create_directories(self) -> None:
        """Create all necessary download directories."""
        directories = [
            getattr(self, "base_download_path", None),
            getattr(self, "youtube_path", None),
            getattr(self, "twitter_path", None),
            getattr(self, "tiktok_path", None),
            getattr(self, "facebook_path", None),
            getattr(self, "instagram_path", None),
            getattr(self, "pinterest_path", None),
        ]
        for directory in directories:
            if directory is not None:
                directory.mkdir(parents=True, exist_ok=True)

    def save(self) -> None:
        """Save current settings to JSON file."""
        settings: dict[str, Any] = {
            "version": self.VERSION,
            "theme_color": self.theme_color,
            "quality": self.quality,
            "format_type": self.format_type,
            "max_workers": self.max_workers,
            "auth": {
                "youtube": {
                    "method": self.auth_method,
                    "browser": self.browser,
                    "cookies_file": self.cookies_file,
                    "channel_name": self.channel_name,
                },
                "twitter": {
                    "cookies_file": self.twitter_cookies_file,
                    "username": self.twitter_username,
                },
                "tiktok": {
                    "cookies_file": self.tiktok_cookies_file,
                    "username": self.tiktok_username,
                },
                "facebook": {
                    "cookies_file": self.facebook_cookies_file,
                },
                "instagram": {
                    "cookies_file": self.instagram_cookies_file,
                },
                "pinterest": {
                    "cookies_file": self.pinterest_cookies_file,
                },
            },
        }
        
        try:
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except OSError:
            # Silently fail - settings will use defaults
            pass

    def load(self) -> None:
        """Load settings from JSON file."""
        if not self.config_file_path.exists():
            return
        
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Theme
            self.theme_color = settings.get("theme_color", self.theme_color)
            
            # Quality/Format
            self.quality = settings.get("quality", self.quality)
            self.format_type = settings.get("format_type", self.format_type)
            self.max_workers = settings.get("max_workers", self.max_workers)
            
            # Auth settings
            auth = settings.get("auth", {})
            
            # YouTube
            yt = auth.get("youtube", {})
            self.auth_method = yt.get("method")
            self.browser = yt.get("browser", "chrome")
            self.cookies_file = yt.get("cookies_file")
            self.channel_name = yt.get("channel_name")
            
            # Validate cookies file exists
            if self.cookies_file and not Path(self.cookies_file).exists():
                self.cookies_file = None
                self.auth_method = None
            
            # Twitter
            tw = auth.get("twitter", {})
            self.twitter_cookies_file = tw.get("cookies_file")
            self.twitter_username = tw.get("username")
            
            if self.twitter_cookies_file and not Path(self.twitter_cookies_file).exists():
                self.twitter_cookies_file = None
                self.twitter_username = None
            
            # TikTok
            tt = auth.get("tiktok", {})
            self.tiktok_cookies_file = tt.get("cookies_file")
            self.tiktok_username = tt.get("username")
            
            if self.tiktok_cookies_file and not Path(self.tiktok_cookies_file).exists():
                self.tiktok_cookies_file = None
                self.tiktok_username = None
            
            # Facebook
            fb = auth.get("facebook", {})
            self.facebook_cookies_file = fb.get("cookies_file")
            
            if self.facebook_cookies_file and not Path(self.facebook_cookies_file).exists():
                self.facebook_cookies_file = None

            # Instagram
            ig = auth.get("instagram", {})
            self.instagram_cookies_file = ig.get("cookies_file")
            if self.instagram_cookies_file and not Path(self.instagram_cookies_file).exists():
                self.instagram_cookies_file = None

            # Pinterest
            pin = auth.get("pinterest", {})
            self.pinterest_cookies_file = pin.get("cookies_file")
            if self.pinterest_cookies_file and not Path(self.pinterest_cookies_file).exists():
                self.pinterest_cookies_file = None
                
        except (json.JSONDecodeError, KeyError, TypeError, OSError):
            # If config is corrupted, use defaults
            pass

    def set_quality(self, choice: str) -> None:
        """Set video quality based on user choice."""
        quality_map = {
            "En İyi": "bestvideo+bestaudio/best",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            "En Düşük": "worstvideo+worstaudio/worst",
        }
        for key, value in quality_map.items():
            if key in choice:
                self.quality = value
                return
        self.quality = "bestvideo+bestaudio/best"

    def set_format(self, choice: str) -> None:
        """Set output format based on user choice."""
        self.format_type = "audio" if "Ses" in choice else "video"

    def get_quality_display(self) -> str:
        """Get human-readable quality string."""
        quality_names = {
            "bestvideo+bestaudio/best": "En İyi",
            "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best": "1080p",
            "bestvideo[height<=720]+bestaudio/best[height<=720]/best": "720p",
            "worstvideo+worstaudio/worst": "En Düşük",
        }
        return quality_names.get(self.quality, "Özel")

    def reset(self) -> None:
        """Reset all settings to defaults."""
        self._set_defaults()
        self.save()
