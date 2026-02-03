"""
Twitter/X Downloader Module
Uses gallery-dl for high-quality Twitter video extraction.
Supports bookmarks and single tweet downloads.
"""

import os
import subprocess
import json
from http.cookiejar import MozillaCookieJar
from typing import Any, Callable

from src.core.base import DownloaderBase, ValidationError, DownloadError
from src.utils.history import DownloadHistory


class TwitterDownloader(DownloaderBase):
    """Twitter video downloader using gallery-dl."""

    def __init__(self, config: Any):
        super().__init__(config)
        self.twitter_download_path = config.twitter_path
        os.makedirs(self.twitter_download_path, exist_ok=True)
        self.history = DownloadHistory(
            config.download_path,
            platform_paths={"twitter": self.twitter_download_path}
        )

    def download(
        self,
        url: str,
        progress_hooks: list[Callable] | None = None,
        skip_duplicate_check: bool = False
    ) -> tuple[bool, str]:
        """
        Download video from a Tweet URL.
        
        Note: progress_hooks is accepted for API compatibility but 
        gallery-dl doesn't support the same hook structure as yt-dlp.
        """
        # Duplicate check
        if not skip_duplicate_check:
            is_dup, dup_date = self.history.is_downloaded(url, "twitter")
            if is_dup:
                return False, f"Bu tweet zaten indirilmiş! ({dup_date})"

        # Check if gallery-dl is installed
        result = subprocess.run(["which", "gallery-dl"], capture_output=True)
        if result.returncode != 0:
            # Fallback check
            import shutil
            if not shutil.which("gallery-dl"):
                return False, "gallery-dl sistemde bulunamadı! Lütfen yükleyin."

        # Build command
        cmd = [
            "gallery-dl",
            "--directory", str(self.twitter_download_path),
            "--filename", "{category}_{id}_{num}.{extension}",
            url
        ]

        # Add cookies if available
        if self.config.twitter_cookies_file:
            cmd.extend(["--cookies", self.config.twitter_cookies_file])

        try:
            # Run gallery-dl
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.history.add_download(url, "twitter")
                return True, "Twitter videosu indirildi!"
            else:
                return False, f"gallery-dl hatası: {result.stderr}"
        except Exception as e:
            return False, f"Sistem hatası: {str(e)}"

    def get_bookmarks(self) -> list[str]:
        """
        Fetch bookmarks using gallery-dl.
        Requires valid cookies.
        """
        if not self.config.twitter_cookies_file:
            return []

        # gallery-dl command to list bookmark URLs
        cmd = [
            "gallery-dl",
            "--cookies", self.config.twitter_cookies_file,
            "--get-urls",
            "https://twitter.com/i/bookmarks"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                urls = [u for u in result.stdout.splitlines() if "status" in u]
                return list(set(urls))
            return []
        except Exception:
            return []

    def download_bookmarks(
        self,
        progress_callback: Callable[[int, int, str, bool, str], None] | None = None
    ) -> tuple[int, int, int, list[str]]:
        """
        Download all bookmarks.
        
        Returns:
            Tuple of (successful, failed, skipped, failed_urls)
        """
        urls = self.get_bookmarks()
        if not urls:
            return 0, 0, 0, []

        successful = 0
        failed = 0
        skipped = 0
        failed_urls = []

        total = len(urls)
        for i, url in enumerate(urls):
            if progress_callback:
                progress_callback(i + 1, total, url, True, "İndiriliyor...")

            is_dup, _ = self.history.is_downloaded(url, "twitter")
            if is_dup:
                skipped += 1
                if progress_callback:
                    progress_callback(i + 1, total, url, True, "Atlandı")
                continue

            success, msg = self.download(url, skip_duplicate_check=True)
            if success:
                successful += 1
                if progress_callback:
                    progress_callback(i + 1, total, url, True, "Tamamlandı")
            else:
                failed += 1
                failed_urls.append(f"{url} | {msg}")
                if progress_callback:
                    progress_callback(i + 1, total, url, False, msg)

        return successful, failed, skipped, failed_urls

    def read_urls_from_file(self, file_path: str) -> list[str]:
        """Read Twitter URLs from a text file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dosya bulunamadı: {file_path}")
            
        urls = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and ("twitter.com" in line or "x.com" in line):
                        urls.append(line)
        except Exception as e:
            raise ValidationError(f"Dosya okuma hatası: {e}")
            
        return urls

    def bulk_download(
        self,
        urls: list[str],
        progress_callback: Callable[[int, int, str, bool, str], None] | None = None
    ) -> tuple[int, int, int, list[str]]:
        """Download multiple Twitter URLs."""
        successful = 0
        failed = 0
        skipped = 0
        failed_urls = []

        total = len(urls)
        for i, url in enumerate(urls):
            if progress_callback:
                progress_callback(i + 1, total, url, True, "İndiriliyor...")

            is_dup, _ = self.history.is_downloaded(url, "twitter")
            if is_dup:
                skipped += 1
                continue

            success, msg = self.download(url, skip_duplicate_check=True)
            if success:
                successful += 1
            else:
                failed += 1
                failed_urls.append(f"{url} | {msg}")

        return successful, failed, skipped, failed_urls

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

        except (OSError, IOError) as e:
            return False, f"Cookie dosyası okunamadı: {e}"
        except Exception as e:
            return False, f"Cookie parse hatası: {e}"

    def get_url_extraction_script(self) -> str:
        """
        Return JavaScript code for extracting Twitter/X video URLs.
        User should run this in browser console.
        """
        return '''
// Twitter/X Video URL Extractor
// 1. Go to a Twitter user's media or your favorites
// 2. Scroll down to load all videos you want
// 3. Open browser console (F12 -> Console)
// 4. Paste and run this script
// 5. Copy the result and save to a .txt file

(function() {
    const videoLinks = new Set();
    
    // Find all status links on the page
    document.querySelectorAll('a[href*="/status/"]').forEach(a => {
        const href = a.href;
        if ((href.includes('twitter.com') || href.includes('x.com')) && href.includes('/status/')) {
            videoLinks.add(href.split('?')[0]); // Remove query params
        }
    });
    
    const urls = Array.from(videoLinks).join('\\n');
    console.log('Found ' + videoLinks.size + ' videos:\\n\\n' + urls);
    
    // Copy to clipboard
    navigator.clipboard.writeText(urls).then(() => {
        console.log('\\n✓ URLs copied to clipboard!');
    }).catch(() => {
        console.log('\\n⚠ Could not copy to clipboard. Select and copy manually.');
    });
    
    return urls;
})();
'''
