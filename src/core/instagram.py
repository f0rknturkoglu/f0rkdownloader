"""
Instagram Media Downloader Module
Uses yt-dlp and gallery-dl dual-engine for reliable Instagram downloads with cookie support.
Supports Reels, Posts, and Videos, single and bulk downloads.
"""

import concurrent.futures
import os
import re
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yt_dlp

from src.core.base import DownloaderBase, ValidationError
from src.utils.history import DownloadHistory


class InstagramDownloader(DownloaderBase):
    """Instagram media downloader using yt-dlp with gallery-dl fallback."""

    SUPPORTED_DOMAINS = ("instagram.com", "instagr.am")

    def __init__(self, config: Any):
        super().__init__(config)
        ig_path = getattr(config, "instagram_path", Path(config.download_path) / "Instagram")
        self.instagram_download_path = Path(ig_path)
        self.instagram_download_path.mkdir(parents=True, exist_ok=True)
        self.history = DownloadHistory(
            config.download_path,
            platform_paths={"instagram": self.instagram_download_path}
        )

    def is_instagram_url(self, url: str) -> bool:
        """Check if URL is a valid Instagram URL."""
        return any(domain in url for domain in self.SUPPORTED_DOMAINS)

    @classmethod
    def normalize_url(cls, url: str) -> str:
        """
        Normalize Instagram URLs by stripping tracking parameters.
        """
        if not url:
            return url
        url = url.strip()
        clean_url = url.split("?")[0].rstrip("/")
        return clean_url

    def _download_with_gallery_dl(self, url: str) -> tuple[bool, str]:
        """
        Fallback downloader for Instagram using gallery-dl.
        """
        gallery_dl_path = self.find_executable("gallery-dl")
        if not gallery_dl_path:
            return False, "gallery-dl sistemde bulunamadı"

        cmd = [
            gallery_dl_path,
            "--directory", str(self.instagram_download_path),
            "--filename", "{id}_{title[:100]}.{extension}",
            url
        ]
        if self.config.instagram_cookies_file and os.path.exists(self.config.instagram_cookies_file):
            cmd.extend(["--cookies", self.config.instagram_cookies_file])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                return True, "gallery-dl ile başarıyla indirildi"
            return False, f"gallery-dl hatası (kod: {result.returncode}): {result.stderr.strip()[:150]}"
        except subprocess.TimeoutExpired:
            return False, "gallery-dl zaman aşımına uğradı (120s)"
        except Exception as e:
            return False, f"gallery-dl çalıştırma hatası: {e!s}"

    def read_urls_from_file(self, file_path: str) -> list[str]:
        """
        Read Instagram URLs from a text file or folder.
        """
        path = Path(file_path)
        if not path.exists():
            raise ValidationError(f"Dosya bulunamadı: {file_path}")

        if path.is_dir():
            candidates = sorted(
                path.glob("*.txt"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            valid_txt = [c for c in candidates if "cookie" not in c.name.lower()]
            if valid_txt:
                path = valid_txt[0]
            else:
                raise ValidationError(f"Belirtilen klasörde geçerli bir .txt URL listesi bulunamadı: {file_path}")

        urls = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    url = line.strip()
                    if url and self.is_instagram_url(url):
                        norm_url = self.normalize_url(url)
                        if norm_url not in urls:
                            urls.append(norm_url)
            return urls
        except Exception as e:
            raise ValidationError(f"Dosya okuma hatası: {e}")

    def download(
        self,
        url: str,
        progress_hooks: list[Callable] | None = None,
        skip_duplicate_check: bool = False
    ) -> tuple[bool, str]:
        """
        Download a single Instagram video or post.
        """
        url = self.normalize_url(url)

        # Duplicate check
        if not skip_duplicate_check:
            is_dup, dup_date = self.history.is_downloaded(url, "instagram")
            if is_dup:
                return False, f"Bu içerik zaten indirilmiş! ({dup_date})"

        ydl_opts = self.get_base_options()
        ydl_opts.update({
            "outtmpl": str(self.instagram_download_path / "%(title).200s [%(id)s].%(ext)s"),
        })

        if self.config.instagram_cookies_file and os.path.exists(self.config.instagram_cookies_file):
            ydl_opts["cookiefile"] = self.config.instagram_cookies_file

        if progress_hooks:
            ydl_opts["progress_hooks"] = progress_hooks

        ytdlp_msg = ""
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                error_code = ydl.download([url])
                if error_code == 0:
                    self.history.add_download(url, "instagram")
                    return True, "Başarıyla indirildi"
                ytdlp_msg = f"yt-dlp hatası (kod: {error_code})"
        except Exception as e:
            ytdlp_msg = f"yt-dlp hatası: {e!s}"

        # Fallback to gallery-dl
        gdl_success, gdl_msg = self._download_with_gallery_dl(url)
        if gdl_success:
            self.history.add_download(url, "instagram")
            return True, "Başarıyla indirildi (gallery-dl fallback)"

        return False, f"{ytdlp_msg} | {gdl_msg}"

    def bulk_download(
        self,
        urls: list[str],
        progress_callback: Callable[[int, int, str, bool, str], None] | None = None,
        skip_duplicates: bool = True,
    ) -> tuple[int, int, int, list[str]]:
        """
        Download multiple Instagram items concurrently.
        """
        if not urls:
            return 0, 0, 0, []

        successful = 0
        failed = 0
        skipped = 0
        failed_urls = []
        total = len(urls)

        # Filter duplicates if requested
        to_download = []
        for url in urls:
            if skip_duplicates:
                is_dup, _ = self.history.is_downloaded(url, "instagram")
                if is_dup:
                    skipped += 1
                    if progress_callback:
                        progress_callback(skipped, total, url, False, "Daha önce indirilmiş (Atlandı)")
                    continue
            to_download.append(url)

        if not to_download:
            return 0, 0, skipped, []

        workers = max(1, min(self.config.max_workers, 4))

        def download_single(item_idx: int, target_url: str):
            success, msg = self.download(target_url, skip_duplicate_check=True)
            return item_idx, target_url, success, msg

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_map = {
                executor.submit(download_single, i + 1, u): u
                for i, u in enumerate(to_download)
            }

            for future in concurrent.futures.as_completed(future_map):
                idx, item_url, success, msg = future.result()
                if success:
                    successful += 1
                else:
                    failed += 1
                    failed_urls.append(item_url)

                if progress_callback:
                    progress_callback(successful + failed + skipped, total, item_url, success, msg)

        return successful, failed, skipped, failed_urls

    def bulk_download_from_file(
        self,
        file_path: str,
        progress_callback: Callable[[int, int, str, bool, str], None] | None = None,
    ) -> tuple[int, int, int, list[str]]:
        """Download items from a text file containing Instagram URLs."""
        urls = self.read_urls_from_file(file_path)
        return self.bulk_download(urls, progress_callback)
