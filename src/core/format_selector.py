"""
Interactive Format Selector Module
Extracts available media formats for a URL and provides structured format choices.
"""

from typing import Any
import yt_dlp


class FormatSelector:
    """Extracts and parses video and audio formats using yt-dlp."""

    @staticmethod
    def extract_available_formats(url: str, cookies_file: str | None = None) -> dict[str, Any]:
        """
        Extract video formats and metadata without downloading.

        Returns:
            dict containing title, duration, thumbnail, and format options list.
        """
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "js_runtimes": {
                "node": {},
                "deno": {},
                "bun": {},
                "quickjs": {},
            },
        }
        if cookies_file:
            ydl_opts["cookiefile"] = cookies_file

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return {"title": "Bilinmeyen Başlık", "formats": []}

        formats = info.get("formats", [])
        title = info.get("title", "Bilinmeyen Başlık")
        duration = info.get("duration", 0)

        # Build options
        available_heights = set()
        for f in formats:
            h = f.get("height")
            if h and f.get("vcodec") != "none":
                available_heights.add(h)

        choices = [
            {
                "label": "Otomatik En İyi Kalite (Önerilen)",
                "format_spec": "bestvideo+bestaudio/best",
                "type": "video",
            }
        ]

        # Resolution hierarchy
        target_resolutions = [
            (2160, "4K UHD (2160p)"),
            (1440, "2K QHD (1440p)"),
            (1080, "Full HD (1080p)"),
            (720, "HD (720p)"),
            (480, "Standart (480p)"),
            (360, "Düşük Boyut (360p)"),
        ]

        for height, label in target_resolutions:
            if any(h >= height for h in available_heights):
                choices.append({
                    "label": f"Video: {label}",
                    "format_spec": f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best",
                    "type": "video",
                })

        # Audio choices
        choices.extend([
            {
                "label": "Sadece Ses: MP3 (320 kbps - Zengin Metadata & Albüm Kapağı)",
                "format_spec": "bestaudio/best",
                "type": "audio",
                "codec": "mp3",
                "quality": "320",
            },
            {
                "label": "Sadece Ses: MP3 (192 kbps - Standart Boyut)",
                "format_spec": "bestaudio/best",
                "type": "audio",
                "codec": "mp3",
                "quality": "192",
            },
            {
                "label": "Sadece Ses: FLAC (Kayıpsız / Lossless)",
                "format_spec": "bestaudio/best",
                "type": "audio",
                "codec": "flac",
                "quality": "0",
            },
        ])

        return {
            "title": title,
            "duration": duration,
            "thumbnail": info.get("thumbnail"),
            "choices": choices,
        }
