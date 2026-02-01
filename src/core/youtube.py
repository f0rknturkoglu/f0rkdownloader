"""
YouTube Downloader Module
Handles YouTube video and playlist downloads.
"""

import os
import shutil
import glob
from typing import Callable

import yt_dlp
from src.core.base import DownloaderBase
from src.utils.history import DownloadHistory


class YoutubeDownloader(DownloaderBase):
    """YouTube video and playlist downloader."""

    def __init__(self, config):
        super().__init__(config)
        self.youtube_path = config.youtube_path
        os.makedirs(self.youtube_path, exist_ok=True)
        self.history = DownloadHistory(
            config.download_path,
            platform_paths={"youtube": self.youtube_path}
        )

    def _find_ffmpeg(self) -> str | None:
        """Find ffmpeg binary location."""
        # Check if ffmpeg is in PATH
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            return os.path.dirname(ffmpeg_path)

        # Check WinGet packages folder
        winget_packages = os.path.expanduser(
            "~\\AppData\\Local\\Microsoft\\WinGet\\Packages"
        )
        if os.path.exists(winget_packages):
            pattern = os.path.join(winget_packages, "**", "ffmpeg.exe")
            matches = glob.glob(pattern, recursive=True)
            if matches:
                return os.path.dirname(matches[0])

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

        # YouTube-specific settings
        ydl_opts.update({
            "outtmpl": self._get_output_template(url),
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
            "format_sort": ["res", "ext:mp4:m4a", "codec:h264"],
            "merge_output_format": "mp4",
        })

        # Audio-only settings
        if self.config.format_type == "audio":
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]

        # Add authentication
        ydl_opts = self._add_auth_options(ydl_opts)

        # Progress tracking
        if progress_hooks:
            ydl_opts["progress_hooks"] = progress_hooks

        # Download
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                # Check if download actually succeeded
                if not info:
                    return False, "Video bilgisi alınamadı!"

                # Check if any formats were available
                formats = info.get("formats", [])
                if not formats and not info.get("entries"):
                    return False, "İndirilebilir format bulunamadı!"

                title = info.get("title", "Bilinmeyen")
                ext = info.get("ext", "mp4")
                filename = f"{title}.{ext}"

                # Add to history only on success
                if "playlist" not in url.lower():
                    self.history.add_download(
                        url, "youtube", title=title, filename=filename)

                return True, "İndirme tamamlandı!"

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            if "Requested format is not available" in error_msg:
                return False, "İndirilebilir format bulunamadı!"
            return False, f"İndirme hatası: {error_msg[:100]}"
        except Exception as e:
            return False, f"Beklenmeyen hata: {str(e)[:100]}"
