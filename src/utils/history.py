"""
Download History Management
Tracks downloaded URLs to prevent duplicate downloads.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path


class DownloadHistory:
    """Manages download history to prevent duplicates."""

    def __init__(self, base_path: str | Path, platform_paths: dict[str, Path] | None = None):
        self.base_path = Path(base_path)
        self.history_file = self.base_path / ".download_history.json"
        self.platform_paths = platform_paths or {}
        self._history: dict[str, dict] = {"youtube": {}, "twitter": {}}
        self._load_history()

    def _load_history(self) -> None:
        """Load history from JSON file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Ensure both platforms exist
                    self._history = {
                        "youtube": data.get("youtube", {}),
                        "twitter": data.get("twitter", {}),
                    }
            except (json.JSONDecodeError, OSError):
                self._history = {"youtube": {}, "twitter": {}}

    def _save_history(self) -> None:
        """Save history to JSON file."""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self._history, f, indent=2, ensure_ascii=False)
        except OSError:
            pass  # Silently fail on save errors

    @staticmethod
    def extract_video_id(url: str, platform: str) -> str | None:
        """Extract unique video ID from URL."""
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
            # https://twitter.com/user/status/1234567890
            # https://x.com/user/status/1234567890
            pattern = r"(?:twitter\.com|x\.com)/\w+/status/(\d+)"
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def is_downloaded(self, url: str, platform: str) -> tuple[bool, str | None]:
        """
        Check if URL was already downloaded AND file still exists.

        Returns:
            Tuple of (is_duplicate, download_date_str)
        """
        video_id = self.extract_video_id(url, platform)
        if not video_id:
            return False, None

        platform_history = self._history.get(platform, {})
        if video_id in platform_history:
            entry = platform_history[video_id]
            filename = entry.get("filename")

            # If we have a filename, check if file still exists
            if filename:
                platform_path = self.platform_paths.get(platform)
                if platform_path:
                    file_path = platform_path / filename
                    if not file_path.exists():
                        # File was deleted, remove from history
                        self._remove_from_history(video_id, platform)
                        return False, None

            return True, entry.get("date")

        return False, None

    def _remove_from_history(self, video_id: str, platform: str) -> None:
        """Remove an entry from history."""
        if platform in self._history and video_id in self._history[platform]:
            del self._history[platform][video_id]
            self._save_history()

    def add_download(
        self,
        url: str,
        platform: str,
        title: str | None = None,
        filename: str | None = None
    ) -> bool:
        """
        Add a download to history.

        Returns:
            True if added, False if already exists
        """
        video_id = self.extract_video_id(url, platform)
        if not video_id:
            return False

        if platform not in self._history:
            self._history[platform] = {}

        # Check if already exists
        if video_id in self._history[platform]:
            return False

        self._history[platform][video_id] = {
            "url": url,
            "title": title,
            "filename": filename,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        self._save_history()
        return True

    def remove_download(self, url: str, platform: str) -> bool:
        """Remove a download from history."""
        video_id = self.extract_video_id(url, platform)
        if not video_id:
            return False

        if platform in self._history and video_id in self._history[platform]:
            del self._history[platform][video_id]
            self._save_history()
            return True

        return False

    def get_stats(self) -> dict[str, int]:
        """Get download statistics."""
        return {
            "youtube": len(self._history.get("youtube", {})),
            "twitter": len(self._history.get("twitter", {})),
            "total": (
                len(self._history.get("youtube", {})) +
                len(self._history.get("twitter", {}))
            ),
        }

    def clear_history(self, platform: str | None = None) -> int:
        """
        Clear download history.

        Args:
            platform: Specific platform to clear, or None for all

        Returns:
            Number of entries cleared
        """
        if platform:
            count = len(self._history.get(platform, {}))
            self._history[platform] = {}
        else:
            count = sum(len(v) for v in self._history.values())
            self._history = {"youtube": {}, "twitter": {}}

        self._save_history()
        return count
