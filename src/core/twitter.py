"""
Twitter/X Downloader Module
Uses gallery-dl for high-quality Twitter video extraction.
Supports bookmarks and single tweet downloads.
"""

import concurrent.futures
import os
import shutil
import subprocess
import threading
from collections.abc import Callable
from http.cookiejar import MozillaCookieJar
from pathlib import Path
from typing import Any

from src.core.base import DownloaderBase, ValidationError
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
        gallery_dl_bin = self.find_executable("gallery-dl")
        if not gallery_dl_bin:
            return False, "gallery-dl sistemde bulunamadı! Lütfen yükleyin."

        # Build command
        cmd = [
            gallery_dl_bin,
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
            return False, f"Sistem hatası: {e!s}"

    def get_bookmarks(self) -> list[str]:
        """
        Fetch bookmarks using gallery-dl.
        Requires valid cookies.
        """
        if not self.config.twitter_cookies_file:
            return []

        gallery_dl_bin = self.find_executable("gallery-dl")
        if not gallery_dl_bin:
            return []

        # gallery-dl command to list bookmark URLs
        cmd = [
            gallery_dl_bin,
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
        return self.bulk_download(urls, progress_callback=progress_callback)

    def read_urls_from_file(self, file_path: str) -> list[str]:
        """Read Twitter URLs from a text file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Dosya bulunamadı: {file_path}")

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
            with open(path, 'r', encoding='utf-8') as f:
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
        """Download multiple Twitter URLs concurrently."""
        if not urls:
            return 0, 0, 0, []

        successful = 0
        failed = 0
        skipped = 0
        failed_urls: list[str] = []
        lock = threading.Lock()

        total = len(urls)
        processed = 0

        pending_urls: list[str] = []
        for url in urls:
            is_dup, _ = self.history.is_downloaded(url, "twitter")
            if is_dup:
                skipped += 1
                if progress_callback:
                    progress_callback(skipped, total, url, True, "Atlandı (Zaten indirilmiş)")
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

        except OSError as e:
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
