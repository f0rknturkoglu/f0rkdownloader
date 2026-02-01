"""
Twitter/X Video Downloader Module
Uses gallery-dl for reliable Twitter downloads (handles cookies better than yt-dlp).
Supports single, bulk, and bookmark downloads.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable

from src.core.base import DownloaderBase
from src.utils.history import DownloadHistory


class TwitterDownloader(DownloaderBase):
    """Twitter/X downloader using gallery-dl."""

    # Supported Twitter/X domains
    SUPPORTED_DOMAINS = ("twitter.com", "x.com")

    def __init__(self, config):
        super().__init__(config)
        self.twitter_download_path = Path(
            self.config.download_path) / "Twitter"
        os.makedirs(self.twitter_download_path, exist_ok=True)
        self.history = DownloadHistory(
            config.download_path,
            platform_paths={"twitter": self.twitter_download_path}
        )

        # gallery-dl executable path (same directory as python)
        python_dir = Path(sys.executable).parent
        if os.name == "nt":
            self.gallery_dl_path = str(python_dir / "gallery-dl.exe")
        else:
            self.gallery_dl_path = str(python_dir / "gallery-dl")

    @staticmethod
    def is_twitter_url(url: str) -> bool:
        """Check if URL is a valid Twitter/X URL."""
        return any(domain in url for domain in TwitterDownloader.SUPPORTED_DOMAINS)

    def read_urls_from_file(self, file_path: str | Path) -> list[str]:
        """Read Twitter/X URLs from a text file."""
        urls = []
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"URL dosyası bulunamadı: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith("#") and self.is_twitter_url(line):
                    urls.append(line)

        return urls

    def _build_gallery_dl_cmd(self, url: str) -> list[str]:
        """Build gallery-dl command with options."""
        cmd = [
            self.gallery_dl_path,
            "--dest", self.twitter_download_path,
            # Flat structure - no subdirectories
            "--directory", ".",
            "--filename", "{author[name]}_{tweet_id}.{extension}",
            "--filter", "extension in ('mp4', 'webm')",  # Only videos
            "--no-mtime",  # Don't set file modification time
        ]

        # Add cookies if configured
        if self.config.twitter_cookies_file:
            cmd.extend(["--cookies", str(self.config.twitter_cookies_file)])

        cmd.append(url)
        return cmd

    def _run_gallery_dl(
        self,
        url: str,
        progress_callback: Callable[[str], None] | None = None
    ) -> bool:
        """
        Run gallery-dl for a single URL.

        Returns:
            True if download successful
        """
        cmd = self._build_gallery_dl_cmd(url)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )

            if progress_callback:
                progress_callback(f"İndiriliyor: {url[:50]}...")

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            return False
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                "gallery-dl bulunamadı! 'pip install gallery-dl' çalıştırın."
            ) from exc

    def download(
        self,
        url: str,
        progress_hooks: list[Callable] | None = None,
        skip_duplicate_check: bool = False
    ) -> tuple[bool, str]:
        """
        Download a single Twitter/X video using gallery-dl.

        Returns:
            Tuple of (success, message)
        """
        if not self.is_twitter_url(url):
            return False, f"Geçersiz Twitter/X URL'si: {url}"

        # Duplicate check
        if not skip_duplicate_check:
            is_dup, dup_date = self.history.is_downloaded(url, "twitter")
            if is_dup:
                return False, f"Bu tweet zaten indirilmiş! ({dup_date})"

        success = self._run_gallery_dl(url)

        if success:
            self.history.add_download(url, "twitter")
            return True, "İndirme tamamlandı!"
        return False, "İndirme başarısız!"

    def bulk_download(
        self,
        urls: list[str],
        progress_callback: Callable[[
            int, int, str, bool, str], None] | None = None,
        skip_duplicates: bool = True,
    ) -> tuple[int, int, int, list[str]]:
        """
        Download multiple Twitter/X videos.

        Args:
            urls: List of Twitter/X URLs to download
            progress_callback: Optional callback(current, total, url, success, message)
            skip_duplicates: Skip already downloaded URLs

        Returns:
            Tuple of (successful_count, failed_count, skipped_count, failed_urls)
        """
        successful = 0
        failed = 0
        skipped = 0
        failed_urls = []

        for i, url in enumerate(urls, 1):
            # Duplicate check
            if skip_duplicates:
                is_dup, dup_date = self.history.is_downloaded(url, "twitter")
                if is_dup:
                    skipped += 1
                    if progress_callback:
                        progress_callback(
                            i, len(urls), url, True, f"Atlandı (zaten var: {dup_date})")
                    continue

            try:
                success = self._run_gallery_dl(url)
                if success:
                    successful += 1
                    self.history.add_download(url, "twitter")
                    if progress_callback:
                        progress_callback(i, len(urls), url, True, "İndirildi")
                else:
                    failed += 1
                    failed_urls.append(url)
                    if progress_callback:
                        progress_callback(i, len(urls), url,
                                          False, "Başarısız")

            except (OSError, subprocess.SubprocessError):
                failed += 1
                failed_urls.append(url)
                if progress_callback:
                    progress_callback(i, len(urls), url, False, "Hata")

        # Save failed URLs
        if failed_urls:
            self._save_failed_urls(failed_urls)

        return successful, failed, skipped, failed_urls

    def _save_failed_urls(self, failed_urls: list[str]) -> None:
        """Save failed URLs to a text file."""
        failed_file = os.path.join(
            self.twitter_download_path, "failed_downloads.txt")
        with open(failed_file, "w", encoding="utf-8") as f:
            for url in failed_urls:
                f.write(url + "\n")

    def bulk_download_from_file(
        self,
        file_path: str | Path,
        progress_callback: Callable[[
            int, int, str, bool, str], None] | None = None,
    ) -> tuple[int, int, int, list[str]]:
        """Download videos from a text file containing Twitter/X URLs."""
        urls = self.read_urls_from_file(file_path)

        if not urls:
            raise ValueError("Dosyada geçerli Twitter/X URL'si bulunamadı!")

        return self.bulk_download(urls, progress_callback)

    def get_bookmarks(self, max_count: int = 100) -> list[dict]:
        """
        Fetch bookmarks from Twitter using gallery-dl.

        Args:
            max_count: Maximum number of bookmarks to fetch

        Returns:
            List of bookmark dicts with url key
        """
        if not self.config.twitter_cookies_file:
            return []

        bookmarks = []
        cmd = [
            self.gallery_dl_path,
            "--cookies", str(self.config.twitter_cookies_file),
            "--dump-json",
            "--range", f"1-{max_count}",
            "https://twitter.com/i/bookmarks"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Bilinmeyen hata"
                print(f"[gallery-dl hata] {error_msg}")
                return []

            # Parse JSON output - gallery-dl returns array format
            try:
                data = json.loads(result.stdout)

                # gallery-dl returns nested arrays: [[type, data], [type, url, data], ...]
                for item in data:
                    if not isinstance(item, list) or len(item) < 2:
                        continue

                    # Type 3 items have video URL
                    if item[0] == 3 and len(item) >= 3:
                        item_data = item[2] if isinstance(
                            item[2], dict) else None
                        if item_data and item_data.get("extension") in ("mp4", "webm"):
                            tweet_id = item_data.get("tweet_id")
                            author = item_data.get("author", {})
                            screen_name = author.get("name") if isinstance(
                                author, dict) else None

                            if tweet_id and screen_name:
                                url = f"https://x.com/{screen_name}/status/{tweet_id}"
                                if not any(b["url"] == url for b in bookmarks):
                                    bookmarks.append({
                                        "url": url,
                                        "tweet_id": tweet_id,
                                        "author": screen_name,
                                    })

            except json.JSONDecodeError as e:
                print(f"[JSON parse hata] {e}")
                return []

        except subprocess.TimeoutExpired:
            print("[gallery-dl] Zaman aşımı")
            return []
        except FileNotFoundError:
            print("[gallery-dl] Kurulu değil!")
            return []

        return bookmarks[:max_count]

    def download_bookmarks(
        self,
        progress_callback: Callable[[
            int, int, str, bool, str], None] | None = None,
        max_count: int = 100,
    ) -> tuple[int, int, int, list[str]]:
        """
        Download all bookmarked videos.

        Returns:
            (successful, failed, skipped, failed_urls)
        """
        bookmarks = self.get_bookmarks(max_count=max_count)
        if not bookmarks:
            return 0, 0, 0, []

        urls = [b["url"] for b in bookmarks]
        return self.bulk_download(urls, progress_callback)

    def validate_twitter_cookies(self, cookies_file: str) -> tuple[bool, str]:
        """
        Test if cookie file is valid for Twitter.

        Returns:
            (success, error_message)
        """
        if not os.path.exists(cookies_file):
            return False, "Cookie dosyası bulunamadı"

        # Validate cookie format
        try:
            from http.cookiejar import MozillaCookieJar
            jar = MozillaCookieJar(cookies_file)
            jar.load(ignore_discard=True, ignore_expires=True)

            has_auth = any(c.name == "auth_token" for c in jar)
            has_ct0 = any(c.name == "ct0" for c in jar)

            if not has_auth:
                return False, "auth_token cookie bulunamadı"
            if not has_ct0:
                return False, "ct0 (CSRF) cookie bulunamadı"

            # Save to config
            self.config.twitter_cookies_file = cookies_file
            return True, ""

        except (OSError, IOError, ValueError) as e:
            return False, f"Cookie dosyası okunamadı: {e}"
