"""
Download History Management
Tracks downloaded URLs to prevent duplicate downloads.
Supports all platforms: YouTube, Twitter, TikTok, Facebook.
"""

import json
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import ClassVar


class DownloadHistory:
    """Manages download history to prevent duplicates across all platforms."""

    # Supported platforms
    PLATFORMS: ClassVar[list[str]] = [
        "youtube", "twitter", "tiktok", "facebook", "instagram", "pinterest"
    ]

    def __init__(
        self, 
        base_path: str, 
        platform_paths: dict[str, Path] | None = None
    ):
        self.base_path = Path(base_path)
        self.history_file = self.base_path / ".download_history.json"
        self.platform_paths = platform_paths or {}
        self._history: dict[str, dict] = {p: {} for p in self.PLATFORMS}
        self._lock = threading.Lock()
        self._load_history()

    def _load_history(self) -> None:
        """Load history from JSON file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Ensure all platforms exist
                    for platform in self.PLATFORMS:
                        self._history[platform] = data.get(platform, {})
            except (json.JSONDecodeError, OSError):
                self._history = {p: {} for p in self.PLATFORMS}

    def _save_history(self) -> None:
        """Save history to JSON file (internal)."""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self._history, f, indent=2, ensure_ascii=False)
        except OSError:
            pass  # Silently fail on save errors

    def save_history(self) -> None:
        """Save history to JSON file (thread-safe public method)."""
        with self._lock:
            self._save_history()

    @staticmethod
    def extract_video_id(url: str, platform: str) -> str | None:
        """
        Extract unique video ID from URL.
        
        Args:
            url: The video URL
            platform: Platform name (youtube, twitter, tiktok, facebook)
            
        Returns:
            Video ID string or None if not found
        """
        url = url.strip()
        
        if platform == "youtube":
            # YouTube video ID patterns
            patterns = [
                r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})",
                r"(?:embed/|shorts/)([a-zA-Z0-9_-]{11})",
            ]
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)

        elif platform == "twitter":
            # Twitter/X status ID pattern
            pattern = r"(?:twitter\.com|x\.com)/\w+/status/(\d+)"
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        elif platform == "tiktok":
            # TikTok video ID patterns
            patterns = [
                r"tiktok\.com/@[\w.-]+/video/(\d+)",  # Standard format
                r"tiktok\.com/video/(\d+)",            # Direct video format
                r"vm\.tiktok\.com/(\w+)",              # Short URL
                r"tiktok\.com/t/(\w+)",                # Another short format
            ]
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)

        elif platform == "facebook":
            # Facebook video ID patterns
            patterns = [
                r"facebook\.com/.+/videos/(\d+)",     # Standard video
                r"facebook\.com/watch/\?v=(\d+)",      # Watch URL
                r"facebook\.com/reel/(\d+)",          # Reel URL
                r"facebook\.com/story\.php\?story_fbid=(\d+)", # Story URL
                r"fb\.watch/(\w+)",                   # Short URL
            ]
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)

        elif platform == "instagram":
            # Instagram post/reel/tv patterns
            patterns = [
                r"(?:instagram\.com|instagr\.am)/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)",
            ]
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)

        elif platform == "pinterest":
            # Pinterest pin patterns
            patterns = [
                r"pinterest\.[a-z.]+/pin/(\d+)",
                r"pin\.it/([A-Za-z0-9_-]+)",
            ]
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
        
        return None

    def add_download(self, url: str, platform: str, auto_save: bool = True) -> bool:
        """
        Add URL to download history.
        
        Args:
            url: The video URL
            platform: Platform name
            auto_save: If True, immediately writes to disk. Set False for bulk operations.
            
        Returns:
            True if added, False if platform not supported
        """
        if platform not in self.PLATFORMS:
            return False
            
        video_id = self.extract_video_id(url, platform)
        if not video_id:
            return False
            
        with self._lock:
            self._history[platform][video_id] = {
                "date": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"),
                "url": url
            }
            if auto_save:
                self._save_history()
        return True

    def is_downloaded(self, url: str, platform: str) -> tuple[bool, str | None]:
        """
        Check if URL was previously downloaded.
        
        Returns:
            Tuple of (is_downloaded, download_date)
        """
        if platform not in self.PLATFORMS:
            return False, None
            
        video_id = self.extract_video_id(url, platform)
        if not video_id:
            # If we can't extract ID, check if file exists on disk (fallback)
            return self._check_file_exists(url, platform, video_id=None), None
            
        with self._lock:
            history_entry = self._history[platform].get(video_id)
        if history_entry:
            return True, history_entry["date"]
            
        # Last resort: check if file actually exists in the download folder
        return self._check_file_exists(url, platform, video_id=video_id), None

    def _check_file_exists(self, url: str, platform: str, video_id: str | None = None) -> bool:
        """Check if video file exists on disk (fallback check)."""
        platform_path = self.platform_paths.get(platform)
        if not platform_path or not platform_path.exists():
            return False
            
        target_id = video_id or self.extract_video_id(url, platform)

        try:
            if target_id:
                for item in platform_path.iterdir():
                    if item.is_file() and target_id in item.name:
                        return True
            else:
                # If ID cannot be extracted from pattern, check URL slug/filename
                url_clean = url.split("?")[0].split("#")[0].rstrip("/")
                slug = Path(url_clean).name
                if slug and len(slug) >= 5:
                    for item in platform_path.iterdir():
                        if item.is_file() and slug in item.name:
                            return True
        except OSError:
            pass
        return False
