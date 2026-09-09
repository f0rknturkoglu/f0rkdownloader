"""
TikTok Video Downloader Module
Uses yt-dlp for reliable TikTok downloads with cookie support.
Supports single, bulk, liked videos, and bookmarked downloads.
Also supports TikTok's official data export (JSON) for liked/favorites.
"""

import concurrent.futures
import json
import os
import re
import subprocess
import threading
import zipfile
from collections.abc import Callable
from datetime import datetime
from http.cookiejar import MozillaCookieJar
from pathlib import Path
from typing import Any

import yt_dlp

from src.core.base import (
    DownloaderBase,
    ValidationError,
)
from src.utils.history import DownloadHistory


class TikTokDownloader(DownloaderBase):
    """TikTok downloader using yt-dlp."""

    SUPPORTED_DOMAINS = ("tiktok.com", "vm.tiktok.com", "vt.tiktok.com")

    def __init__(self, config: Any):
        super().__init__(config)
        self.tiktok_download_path = Path(config.tiktok_path)
        self.tiktok_download_path.mkdir(parents=True, exist_ok=True)
        self.history = DownloadHistory(
            config.download_path,
            platform_paths={"tiktok": self.tiktok_download_path}
        )

    def is_tiktok_url(self, url: str) -> bool:
        """Check if URL is a valid TikTok URL."""
        return any(domain in url for domain in self.SUPPORTED_DOMAINS)

    @classmethod
    def normalize_url(cls, url: str) -> str:
        """
        Normalize TikTok URLs to canonical standard format.
        Direct URLs like 'tiktok.com/video/<id>' (without @user) cause TikTok
        web router to redirect to '/404?fromUrl=...' when fetched by download engines.
        Rewriting to 'https://www.tiktok.com/@video/video/<id>' allows both yt-dlp
        and gallery-dl to extract and download the video reliably.
        """
        if not url:
            return url
        url = url.strip()
        clean_url = url.split("?")[0].rstrip("/")
        # Check if URL contains /video/<digits> without any username (@...)
        match = re.search(r"tiktok\.com/video/(\d+)", clean_url)
        if match:
            video_id = match.group(1)
            return f"https://www.tiktok.com/@video/video/{video_id}"
        return clean_url

    def _download_with_gallery_dl(self, url: str) -> tuple[bool, str]:
        """
        Fallback downloader for TikTok using gallery-dl.
        """
        gallery_dl_path = self.find_executable("gallery-dl")
        if not gallery_dl_path:
            return False, "gallery-dl sistemde bulunamadı"

        cmd = [
            gallery_dl_path,
            "--directory", str(self.tiktok_download_path),
            "--filename", "{id}_{title[:100]}.{extension}",
            url
        ]
        if self.config.tiktok_cookies_file and os.path.exists(self.config.tiktok_cookies_file):
            cmd.extend(["--cookies", self.config.tiktok_cookies_file])

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
        Read TikTok URLs from a text file and normalize them.
        
        Args:
            file_path: Path to the file containing URLs
            
        Returns:
            List of valid TikTok URLs
            
        Raises:
            ValidationError: If file not found or unreadable
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
                    if url and self.is_tiktok_url(url):
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
        Download a single TikTok video using yt-dlp with gallery-dl fallback.

        Returns:
            Tuple of (success, message)
        """
        url = self.normalize_url(url)

        # Duplicate check
        if not skip_duplicate_check:
            is_dup, dup_date = self.history.is_downloaded(url, "tiktok")
            if is_dup:
                return False, f"Bu video zaten indirilmiş! ({dup_date})"

        ydl_opts = self.get_base_options()
        ydl_opts.update({
            "outtmpl": str(self.tiktok_download_path / "%(title).200s [%(id)s].%(ext)s"),
        })

        if self.config.tiktok_cookies_file and os.path.exists(self.config.tiktok_cookies_file):
            ydl_opts["cookiefile"] = self.config.tiktok_cookies_file

        if progress_hooks:
            ydl_opts["progress_hooks"] = progress_hooks

        ytdlp_msg = ""
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                error_code = ydl.download([url])
                if error_code == 0:
                    self.history.add_download(url, "tiktok")
                    return True, "Başarıyla indirildi"
                ytdlp_msg = f"yt-dlp hatası (kod: {error_code})"
        except Exception as e:
            ytdlp_msg = f"yt-dlp hatası: {e!s}"

        # Otomatik motor yedeği (Fallback): gallery-dl
        gdl_success, gdl_msg = self._download_with_gallery_dl(url)
        if gdl_success:
            self.history.add_download(url, "tiktok")
            return True, "Başarıyla indirildi (gallery-dl fallback)"

        return False, f"{ytdlp_msg} | {gdl_msg}"

    def bulk_download(
        self,
        urls: list[str],
        progress_callback: Callable[[int, int, str, bool, str], None] | None = None,
        skip_duplicates: bool = True,
    ) -> tuple[int, int, int, list[str]]:
        """
        Download multiple TikTok videos concurrently.

        Args:
            urls: List of TikTok URLs to download
            progress_callback: Optional callback(current, total, url, success, message)
            skip_duplicates: Skip already downloaded URLs

        Returns:
            Tuple of (successful, failed, skipped, failed_urls)
        """
        if not urls:
            return 0, 0, 0, []

        successful = 0
        failed = 0
        skipped = 0
        failed_urls = []
        lock = threading.Lock()

        total = len(urls)
        processed = 0

        urls = [self.normalize_url(u) for u in urls if u]
        pending_urls: list[str] = []
        for url in urls:
            if skip_duplicates:
                is_dup, _ = self.history.is_downloaded(url, "tiktok")
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

            success, message = self.download(target_url, skip_duplicate_check=True)

            with lock:
                if success:
                    successful += 1
                    if progress_callback:
                        progress_callback(curr_idx, total, target_url, True, "Tamamlandı")
                else:
                    failed += 1
                    failed_urls.append(f"{target_url} | {message}")
                    if progress_callback:
                        progress_callback(curr_idx, total, target_url, False, message)

        if max_workers > 1 and len(pending_urls) > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                list(executor.map(_worker, pending_urls))
        else:
            for u in pending_urls:
                _worker(u)

        self.history.save_history()

        if failed_urls:
            self._save_failed_urls(failed_urls)

        return successful, failed, skipped, failed_urls

    def _save_failed_urls(self, failed_urls: list[str]) -> None:
        """Save failed URLs to a text file."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            failed_file = self.tiktok_download_path / f"failed_downloads_{timestamp}.txt"
            with open(failed_file, "w", encoding="utf-8") as f:
                f.write("\n".join(failed_urls))
        except Exception:
            pass

    def bulk_download_from_file(
        self,
        file_path: str,
        progress_callback: Callable[[int, int, str, bool, str], None] | None = None,
    ) -> tuple[int, int, int, list[str]]:
        """Download videos from a text file containing TikTok URLs."""
        urls = self.read_urls_from_file(file_path)
        return self.bulk_download(urls, progress_callback)

    def download_liked_videos(
        self,
        urls_file: str,
        progress_callback: Callable[[int, int, str, bool, str], None] | None = None,
    ) -> tuple[int, int, int, list[str]]:
        """
        Download liked videos from a URL list file.

        TikTok API doesn't allow direct access to liked videos,
        so user must export URLs using browser console script.

        Returns:
            (successful, failed, skipped, failed_urls)
        """
        return self.bulk_download_from_file(urls_file, progress_callback)

    def download_bookmarked_videos(
        self,
        urls_file: str,
        progress_callback: Callable[[int, int, str, bool, str], None] | None = None,
    ) -> tuple[int, int, int, list[str]]:
        """
        Download bookmarked/favorited videos from a URL list file.

        TikTok API doesn't allow direct access to bookmarks,
        so user must export URLs using browser console script.

        Returns:
            (successful, failed, skipped, failed_urls)
        """
        return self.bulk_download_from_file(urls_file, progress_callback)

    def parse_tiktok_data_export(self, file_path: str) -> dict[str, list[str]]:
        """
        Parse TikTok's official data export file (ZIP or JSON).
        
        TikTok allows users to download their data from the app:
        Settings > Account > Download your data > Request data (JSON format)
        
        Args:
            file_path: Path to the exported ZIP or JSON file
            
        Returns:
            Dict with 'liked', 'favorites', 'watched' URL lists
            
        Raises:
            ValidationError: If file not found or invalid format
        """
        path = Path(file_path)
        if not path.exists():
            raise ValidationError(f"Dosya bulunamadı: {file_path}")

        results = {
            "liked": [],
            "favorites": [],
            "watched": []
        }

        if path.suffix == ".zip":
            results = self._parse_tiktok_zip(path)
        elif path.suffix == ".json":
            results = self._parse_tiktok_json(path)
        else:
            raise ValidationError("Sadece ZIP veya JSON formatındaki TikTok verileri destekleniyor.")

        return results

    def _parse_tiktok_zip(self, zip_path: Path) -> dict[str, list[str]]:
        """Parse TikTok data export ZIP file."""
        results = {"liked": [], "favorites": [], "watched": []}
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                # Look for video list files
                for name in z.namelist():
                    if "Video Reviews" in name and name.endswith(".json"):
                        # This usually contains liked videos
                        with z.open(name) as f:
                            data = json.load(f)
                            results["liked"] = self._extract_urls_from_json(data, "liked")
                    
                    elif "Favorite Videos" in name and name.endswith(".json"):
                        with z.open(name) as f:
                            data = json.load(f)
                            results["favorites"] = self._extract_urls_from_json(data, "favorites")
        except Exception as e:
            raise ValidationError(f"TikTok ZIP açma hatası: {e}")
            
        return results

    def _parse_tiktok_json(self, json_path: Path) -> dict[str, list[str]]:
        """Parse a single TikTok JSON data file."""
        result = {"liked": [], "favorites": [], "watched": []}
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # TikTok JSON structure varies. Try to find potential lists.
            # Activity > Video Reviews > VideoList
            activity = data.get("Activity", {})
            
            # Liked videos
            liked_data = activity.get("Video Reviews", {}).get("VideoList", [])
            result["liked"] = self._extract_urls_from_list(liked_data)
            
            # Favorites
            fav_data = activity.get("Favorite Videos", {}).get("FavoriteVideoList", [])
            result["favorites"] = self._extract_urls_from_list(fav_data)
            
        except Exception as e:
            raise ValidationError(f"TikTok JSON ayrıştırma hatası: {e}")
            
        return result

    def _extract_urls_from_list(self, items: list) -> list[str]:
        """Extract TikTok URLs from a list of items."""
        urls: list[str] = []
        
        for item in items:
            url: str | None = None
            
            if isinstance(item, str):
                # Direct URL string
                if "tiktok.com" in item:
                    url = item
            elif isinstance(item, dict):
                # Try various field names
                url = (
                    item.get("Link") or
                    item.get("link") or
                    item.get("URL") or
                    item.get("url") or
                    item.get("VideoLink") or
                    item.get("video_url") or
                    item.get("share_url")
                )
                
                # Some exports have nested structure
                if not url and "video" in item:
                    video_data = item.get("video", {})
                    if isinstance(video_data, dict):
                        url = video_data.get("url") or video_data.get("link")
            
            if url and "tiktok.com" in url:
                # Clean URL (remove query params)
                clean_url = url.split("?")[0]
                if clean_url not in urls:
                    urls.append(clean_url)
        
        return urls

    def _extract_urls_from_json(
        self, 
        data: dict | list, 
        category: str
    ) -> list[str]:
        """Extract URLs from JSON data based on category."""
        if isinstance(data, list):
            return self._extract_urls_from_list(data)
        elif isinstance(data, dict):
            # Try to find the relevant list in the dict
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0:
                    return self._extract_urls_from_list(value)
        return []

    def get_data_export_urls(
        self,
        file_path: str,
        category: str = "liked"
    ) -> list[str]:
        """
        Get URLs from TikTok data export for a specific category.
        
        Args:
            file_path: Path to TikTok data export (ZIP or JSON)
            category: One of 'liked', 'favorites', 'watched'
            
        Returns:
            List of TikTok video URLs
        """
        all_data = self.parse_tiktok_data_export(file_path)
        return all_data.get(category, [])

    def validate_tiktok_cookies(self, cookies_file: str) -> tuple[bool, str]:
        """
        Test if cookie file is valid for TikTok.

        Returns:
            (success, error_message)
        """
        if not os.path.exists(cookies_file):
            return False, "Cookie dosyası bulunamadı"

        # Validate cookie format
        try:
            jar = MozillaCookieJar(cookies_file)
            jar.load(ignore_discard=True, ignore_expires=True)

            # Check for TikTok-specific cookies
            has_session = any(
                c.name in ("sessionid", "sessionid_ss", "sid_guard", "sid_tt")
                for c in jar
            )
            has_tiktok_domain = any(
                "tiktok.com" in (c.domain or "")
                for c in jar
            )

            if not has_tiktok_domain:
                return False, "TikTok cookie'leri bulunamadı (domain kontrolü)"

            if not has_session:
                return False, "Oturum cookie'si bulunamadı (sessionid)"

            # Save to config
            self.config.tiktok_cookies_file = cookies_file
            return True, ""

        except OSError as e:
            return False, f"Cookie dosyası okunamadı: {e}"
        except Exception as e:
            return False, f"Cookie parse hatası: {e}"

    def get_url_extraction_script(self) -> str:
        """
        Return JavaScript code for extracting TikTok video URLs.
        User should run this in browser console on their liked/favorites page.
        """
        return '''
// TikTok Liked/Favorites URL Extractor
// 1. Go to your liked videos or favorites page on TikTok
// 2. Scroll down to load all videos you want
// 3. Open browser console (F12 -> Console)
// 4. Paste and run this script
// 5. Copy the result and save to a .txt file

(function() {
    const videoLinks = new Set();
    
    // Find all video links on the page
    document.querySelectorAll('a[href*="/video/"]').forEach(a => {
        const href = a.href;
        if (href.includes('tiktok.com') && href.includes('/video/')) {
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
