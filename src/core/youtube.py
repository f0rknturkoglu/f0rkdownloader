"""
YouTube Downloader Module
Handles YouTube video and playlist downloads.
"""

import concurrent.futures
import glob
import os
import shutil
import threading
from collections.abc import Callable
from typing import Any

import yt_dlp

from src.core.base import DownloaderBase
from src.utils.history import DownloadHistory


class YoutubeDownloader(DownloaderBase):
    """YouTube video and playlist downloader."""

    def __init__(self, config: Any):
        super().__init__(config)
        self.youtube_path = config.youtube_path
        os.makedirs(self.youtube_path, exist_ok=True)
        self.history = DownloadHistory(
            config.download_path,
            platform_paths={"youtube": self.youtube_path}
        )
        self._cached_ffmpeg_path: str | None = None
        self._ffmpeg_searched: bool = False

    def _find_ffmpeg(self) -> str | None:
        """Find ffmpeg binary location with caching."""
        if self._ffmpeg_searched:
            return self._cached_ffmpeg_path

        self._ffmpeg_searched = True

        # Check if ffmpeg is in PATH
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            self._cached_ffmpeg_path = os.path.dirname(ffmpeg_path)
            return self._cached_ffmpeg_path

        # Check WinGet packages folder
        winget_packages = os.path.expanduser(
            "~\\AppData\\Local\\Microsoft\\WinGet\\Packages"
        )
        if os.path.exists(winget_packages):
            pattern = os.path.join(winget_packages, "**", "ffmpeg.exe")
            matches = glob.glob(pattern, recursive=True)
            if matches:
                self._cached_ffmpeg_path = os.path.dirname(matches[0])
                return self._cached_ffmpeg_path

        return None

    def _get_output_template(self, url: str) -> str:
        """Get output path template based on URL type."""
        if "playlist" in url.lower():
            return os.path.join(
                self.youtube_path, "%(playlist_title)s", "%(title)s.%(ext)s"
            )
        return os.path.join(self.youtube_path, "%(title)s.%(ext)s")

    def _add_auth_options(self, options: dict) -> dict:
        """Add authentication options based on configured method."""
        if self.config.auth_method == "cookies_file" and self.config.cookies_file:
            options["cookiefile"] = self.config.cookies_file
        elif self.config.auth_method == "browser" and self.config.browser:
            options["cookiesfrombrowser"] = (self.config.browser,)
        return options

    def search(self, query: str, max_results: int = 10) -> list[dict]:
        """
        Search YouTube and return results.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of video info dictionaries
        """
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "default_search": "ytsearch",
            "js_runtimes": {
                "node": {},
                "deno": {},
                "bun": {},
                "quickjs": {},
            },
        }
        ydl_opts = self._add_auth_options(ydl_opts)

        search_query = f"ytsearch{max_results}:{query}"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(search_query, download=False)

            if not result or "entries" not in result:
                return []

            videos = []
            for entry in result["entries"]:
                if entry:
                    videos.append({
                        "title": entry.get("title", "Bilinmeyen"),
                        "url": entry.get("url", ""),
                        "duration": entry.get("duration", 0),
                        "channel": entry.get("channel", entry.get("uploader", "Bilinmeyen")),
                        "view_count": entry.get("view_count", 0),
                    })
            return videos

    def download(
        self,
        url: str,
        progress_hooks: list[Callable] | None = None,
        skip_duplicate_check: bool = False
    ) -> tuple[bool, str]:
        """
        Download a YouTube video or playlist.

        Args:
            url: YouTube video or playlist URL
            progress_hooks: Optional progress callback functions
            skip_duplicate_check: Skip duplicate check (for playlists)

        Returns:
            Tuple of (success, message)
        """
        # Duplicate check (skip for playlists)
        if not skip_duplicate_check and "playlist" not in url.lower():
            is_dup, dup_date = self.history.is_downloaded(url, "youtube")
            if is_dup:
                return False, f"Bu video zaten indirilmiş! ({dup_date})"

        # Start with base options
        ydl_opts = self.get_base_options()

        # Find ffmpeg path
        ffmpeg_path = self._find_ffmpeg()
        if ffmpeg_path:
            ydl_opts["ffmpeg_location"] = ffmpeg_path

        # Add auth
        ydl_opts = self._add_auth_options(ydl_opts)

        # Set output template
        ydl_opts["outtmpl"] = self._get_output_template(url)

        # Add hooks
        if progress_hooks:
            ydl_opts["progress_hooks"] = progress_hooks

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                error_code = ydl.download([url])
                if error_code == 0:
                    # Save history
                    if "playlist" not in url.lower():
                        self.history.add_download(url, "youtube")
                    return True, "İndirme başarılı!"
                else:
                    # If cookies caused failure or bot challenge, retry anonymously
                    if "cookiefile" in ydl_opts or "cookiesfrombrowser" in ydl_opts:
                        fallback_opts = dict(ydl_opts)
                        fallback_opts.pop("cookiefile", None)
                        fallback_opts.pop("cookiesfrombrowser", None)
                        try:
                            with yt_dlp.YoutubeDL(fallback_opts) as fb_ydl:
                                fb_code = fb_ydl.download([url])
                                if fb_code == 0:
                                    if "playlist" not in url.lower():
                                        self.history.add_download(url, "youtube")
                                    return True, "İndirme başarılı! (Çerez koruması aşılarak anonim modda tamamlandı)"
                        except Exception:
                            pass
                    return False, f"yt-dlp hatası (kod: {error_code})"
        except Exception as e:
            if "cookiefile" in ydl_opts or "cookiesfrombrowser" in ydl_opts:
                fallback_opts = dict(ydl_opts)
                fallback_opts.pop("cookiefile", None)
                fallback_opts.pop("cookiesfrombrowser", None)
                try:
                    with yt_dlp.YoutubeDL(fallback_opts) as fb_ydl:
                        fb_code = fb_ydl.download([url])
                        if fb_code == 0:
                            if "playlist" not in url.lower():
                                self.history.add_download(url, "youtube")
                            return True, "İndirme başarılı! (Çerez koruması aşılarak anonim modda tamamlandı)"
                except Exception:
                    pass
            return False, str(e)

    def read_urls_from_file(self, file_path: str) -> list[str]:
        """Read YouTube URLs from a text file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dosya bulunamadı: {file_path}")
            
        urls = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and ("youtube.com" in line or "youtu.be" in line):
                    urls.append(line)
        return urls

    def bulk_download(
        self,
        urls: list[str],
        progress_callback: Callable[[int, int, str, bool, str], None] | None = None,
        skip_duplicates: bool = True,
    ) -> tuple[int, int, int, list[str]]:
        """
        Download multiple YouTube videos concurrently.
        
        Returns:
            Tuple of (successful, failed, skipped, failed_urls)
        """
        successful = 0
        failed = 0
        skipped = 0
        failed_urls: list[str] = []
        lock = threading.Lock()
        
        total = len(urls)
        processed = 0

        pending_urls: list[str] = []
        for url in urls:
            if skip_duplicates and "playlist" not in url.lower():
                is_dup, dup_date = self.history.is_downloaded(url, "youtube")
                if is_dup:
                    skipped += 1
                    if progress_callback:
                        progress_callback(skipped, total, url, True, f"Atlandı ({dup_date})")
                    continue
            pending_urls.append(url)

        max_workers = getattr(self.config, "max_workers", 3)
        max_workers = max(1, min(max_workers, 5))

        def _worker(target_url: str):
            nonlocal successful, failed, processed
            curr_idx = 0
            with lock:
                processed += 1
                curr_idx = processed + skipped
                if progress_callback:
                    progress_callback(curr_idx, total, target_url, True, "İndiriliyor...")
            
            success, msg = self.download(target_url, skip_duplicate_check=True)
            
            with lock:
                if success:
                    successful += 1
                    if progress_callback:
                        progress_callback(curr_idx, total, target_url, True, "Tamamlandı")
                else:
                    failed += 1
                    failed_urls.append(f"{target_url} | {msg}")
                    if progress_callback:
                        progress_callback(curr_idx, total, target_url, False, msg)

        if max_workers > 1 and len(pending_urls) > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                list(executor.map(_worker, pending_urls))
        else:
            for u in pending_urls:
                _worker(u)

        self.history.save_history()
        return successful, failed, skipped, failed_urls
