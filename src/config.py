import os
from pathlib import Path


class Config:
    """Application configuration management."""

    # Application info
    APP_NAME = "f0rkn_d0wnl0ader"
    VERSION = "2.0.0"

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

        # YouTube settings
        # "bestvideo+bestaudio/best" = En iyi video + en iyi ses VEYA en iyi birleşik format
        self.quality = "bestvideo+bestaudio/best"
        self.format_type = "video"  # video veya audio

        # YouTube Authentication settings
        self.auth_method: str | None = None  # 'browser', 'cookies_file' veya None
        self.browser: str | None = "chrome"  # Varsayılan tarayıcı
        # Cookie dosyası yolu (Netscape format)
        self.cookies_file: str | None = None
        self.channel_name: str | None = None  # Giriş yapan kullanıcının kanal adı

        # Twitter/X Authentication settings
        self.twitter_cookies_file: str | None = None  # Twitter cookie dosyası
        self.twitter_username: str | None = None  # Twitter kullanıcı adı

        # TikTok Authentication settings
        self.tiktok_cookies_file: str | None = None  # TikTok cookie dosyası
        self.tiktok_username: str | None = None  # TikTok kullanıcı adı

        # Facebook Authentication
        self.facebook_cookies_file: str | None = None

        # Bulk download settings
        self.bulk_urls_file: str | None = None  # Path to bulk URLs file

        # Theme settings
        self.theme_color = "ubuntu"  # Default theme color

        # Create directories
        self._create_directories()

    def _create_directories(self):
        """Create all necessary download directories."""
        directories = [
            self.base_download_path,
            self.youtube_path,
            self.twitter_path,
            self.tiktok_path,
            self.facebook_path,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def set_quality(self, choice: str) -> None:
        """Set video quality based on user choice."""
        # Format: preferred/fallback - eğer tercih edilen format yoksa fallback kullanılır
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
        # Default to best quality
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
