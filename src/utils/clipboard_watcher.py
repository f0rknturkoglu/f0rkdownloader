"""
Clipboard Watcher Module
Monitors system clipboard in the background using pyperclip.
Detects supported media links and invokes a handler to download or queue them.
"""

import re
import threading
import time
from collections.abc import Callable
from typing import Any

try:
    import pyperclip
except ImportError:
    pyperclip = None


class ClipboardWatcher:
    """Monitors system clipboard for media URLs across YouTube, Twitter, TikTok, Facebook, Instagram, Pinterest."""

    URL_PATTERNS = [
        ("youtube", re.compile(r"https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)[a-zA-Z0-9_-]+")),
        ("twitter", re.compile(r"https?://(?:www\.)?(?:twitter\.com|x\.com)/\w+/status/\d+")),
        ("tiktok", re.compile(r"https?://(?:www\.)?(?:tiktok\.com/(?:@[\w.-]+/video/\d+|video/\d+)|vm\.tiktok\.com/\w+|vt\.tiktok\.com/\w+)")),
        ("facebook", re.compile(r"https?://(?:www\.|m\.|web\.)?facebook\.com/(?:watch/\?v=\d+|.+/videos/\d+|reel/\d+|share/[rv]/\w+)")),
        ("instagram", re.compile(r"https?://(?:www\.)?(?:instagram\.com|instagr\.am)/(?:p|reel|reels|tv)/[A-Za-z0-9_-]+")),
        ("pinterest", re.compile(r"https?://(?:[a-zA-Z0-9-]+\.)?(?:pinterest\.[a-z.]+/pin/\d+|pin\.it/[A-Za-z0-9_-]+)")),
    ]

    def __init__(self, on_link_found: Callable[[str, str], None] | None = None, check_interval: float = 1.0):
        self.on_link_found = on_link_found
        self.check_interval = check_interval
        self._running = False
        self._thread: threading.Thread | None = None
        self._seen_urls: set[str] = set()
        self._last_raw_text = ""

    def detect_platform(self, text: str) -> tuple[str, str] | None:
        """
        Check if text contains a supported URL.
        Returns tuple of (url, platform) or None.
        """
        text = text.strip()
        for platform, pattern in self.URL_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(0), platform
        return None

    def _loop(self) -> None:
        while self._running:
            try:
                if pyperclip:
                    text = pyperclip.paste()
                    if text and text != self._last_raw_text:
                        self._last_raw_text = text
                        result = self.detect_platform(text)
                        if result:
                            url, platform = result
                            if url not in self._seen_urls:
                                self._seen_urls.add(url)
                                if self.on_link_found:
                                    self.on_link_found(url, platform)
            except Exception:
                pass
            time.sleep(self.check_interval)

    def start(self) -> bool:
        """Start the clipboard watcher daemon."""
        if not pyperclip:
            return False
        if self._running:
            return True

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        """Stop the clipboard watcher."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    @property
    def is_running(self) -> bool:
        return self._running
