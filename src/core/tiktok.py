"""
TikTok Video Downloader Module
Uses yt-dlp for reliable TikTok downloads with cookie support.
Supports single, bulk, liked videos, and bookmarked downloads.
Also supports TikTok's official data export (JSON) for liked/favorites.
"""

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Callable

from src.core.base import DownloaderBase
from src.utils.history import DownloadHistory


class TikTokDownloader(DownloaderBase):
    """TikTok downloader using yt-dlp."""

    # Supported TikTok domains
    SUPPORTED_DOMAINS = ("tiktok.com", "vm.tiktok.com", "vt.tiktok.com")

    def __init__(self, config):
        super().__init__(config)
        self.tiktok_download_path = Path(
            self.config.download_path) / "TikTok"
        os.makedirs(self.tiktok_download_path, exist_ok=True)
        self.history = DownloadHistory(
            config.download_path,
            platform_paths={"tiktok": self.tiktok_download_path}
        )

        # yt-dlp executable path
        python_dir = Path(sys.executable).parent
        if os.name == "nt":
            self.ytdlp_path = str(python_dir / "yt-dlp.exe")
        else:
            self.ytdlp_path = str(python_dir / "yt-dlp")

        # Check if yt-dlp exists, otherwise use module call
        if not os.path.exists(self.ytdlp_path):
            self.ytdlp_path = "yt-dlp"

    @staticmethod
    def is_tiktok_url(url: str) -> bool:
        """Check if URL is a valid TikTok URL."""
        return any(domain in url.lower() for domain in TikTokDownloader.SUPPORTED_DOMAINS)

    def read_urls_from_file(self, file_path: str | Path) -> list[str]:
        """Read TikTok URLs from a text file."""
        urls = []
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"URL dosyası bulunamadı: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith("#") and self.is_tiktok_url(line):
                    urls.append(line)

        return urls

    def _build_ytdlp_cmd(self, url: str) -> list[str]:
        """Build yt-dlp command with options."""
        output_template = str(
            self.tiktok_download_path / "%(uploader)s_%(id)s.%(ext)s")

        cmd = [
            self.ytdlp_path,
            "--no-warnings",
            "--no-playlist",
            "-f", "best",  # Best quality
            "-o", output_template,
            "--no-mtime",  # Don't set file modification time
            "--no-check-certificates",
        ]

        # Add cookies if configured
        if self.config.tiktok_cookies_file and os.path.exists(self.config.tiktok_cookies_file):
            cmd.extend(["--cookies", str(self.config.tiktok_cookies_file)])

        cmd.append(url)
        return cmd

    def _run_ytdlp(
        self,
        url: str,
        progress_callback: Callable[[str], None] | None = None
    ) -> tuple[bool, str]:
        """
        Run yt-dlp for a single URL.

        Returns:
            Tuple of (success, message)
        """
        cmd = self._build_ytdlp_cmd(url)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )

            if progress_callback:
                progress_callback(f"İndiriliyor: {url[:50]}...")

            if result.returncode == 0:
                return True, "İndirme tamamlandı!"

            # Parse error message
            error = result.stderr.strip() if result.stderr else result.stdout.strip()
            if "Private video" in error or "private" in error.lower():
                return False, "Bu video gizli veya silinmiş"
            if "Video unavailable" in error:
                return False, "Video mevcut değil"
            if "Login required" in error:
                return False, "Giriş gerekli - Cookie dosyası ekleyin"

            return False, error[:100] if error else "Bilinmeyen hata"

        except subprocess.TimeoutExpired:
            return False, "Zaman aşımı (180s)"
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                "yt-dlp bulunamadı! 'pip install yt-dlp' çalıştırın."
            ) from exc

    def download(
        self,
        url: str,
        progress_hooks: list[Callable] | None = None,
        skip_duplicate_check: bool = False
    ) -> tuple[bool, str]:
        """
        Download a single TikTok video using yt-dlp.

        Returns:
            Tuple of (success, message)
        """
        if not self.is_tiktok_url(url):
            return False, f"Geçersiz TikTok URL'si: {url}"

        # Duplicate check
        if not skip_duplicate_check:
            is_dup, dup_date = self.history.is_downloaded(url, "tiktok")
            if is_dup:
                return False, f"Bu video zaten indirilmiş! ({dup_date})"

        success, message = self._run_ytdlp(url)

        if success:
            self.history.add_download(url, "tiktok")
            return True, "İndirme tamamlandı!"
        return False, message

    def bulk_download(
        self,
        urls: list[str],
        progress_callback: Callable[[
            int, int, str, bool, str], None] | None = None,
        skip_duplicates: bool = True,
    ) -> tuple[int, int, int, list[str]]:
        """
        Download multiple TikTok videos.

        Args:
            urls: List of TikTok URLs to download
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
                is_dup, dup_date = self.history.is_downloaded(url, "tiktok")
                if is_dup:
                    skipped += 1
                    if progress_callback:
                        progress_callback(
                            i, len(urls), url, True, f"Atlandı (zaten var: {dup_date})")
                    continue

            try:
                success, message = self._run_ytdlp(url)
                if success:
                    successful += 1
                    self.history.add_download(url, "tiktok")
                    if progress_callback:
                        progress_callback(i, len(urls), url, True, "İndirildi")
                else:
                    failed += 1
                    failed_urls.append(url)
                    if progress_callback:
                        progress_callback(i, len(urls), url, False, message)

            except (OSError, subprocess.SubprocessError) as e:
                failed += 1
                failed_urls.append(url)
                if progress_callback:
                    progress_callback(i, len(urls), url, False, str(e)[:50])

        # Save failed URLs
        if failed_urls:
            self._save_failed_urls(failed_urls)

        return successful, failed, skipped, failed_urls

    def _save_failed_urls(self, failed_urls: list[str]) -> None:
        """Save failed URLs to a text file."""
        failed_file = os.path.join(
            self.tiktok_download_path, "failed_downloads.txt")
        with open(failed_file, "w", encoding="utf-8") as f:
            for url in failed_urls:
                f.write(url + "\n")

    def bulk_download_from_file(
        self,
        file_path: str | Path,
        progress_callback: Callable[[
            int, int, str, bool, str], None] | None = None,
    ) -> tuple[int, int, int, list[str]]:
        """Download videos from a text file containing TikTok URLs."""
        urls = self.read_urls_from_file(file_path)

        if not urls:
            raise ValueError("Dosyada geçerli TikTok URL'si bulunamadı!")

        return self.bulk_download(urls, progress_callback)

    def download_liked_videos(
        self,
        urls_file: str | Path,
        progress_callback: Callable[[
            int, int, str, bool, str], None] | None = None,
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
        urls_file: str | Path,
        progress_callback: Callable[[
            int, int, str, bool, str], None] | None = None,
    ) -> tuple[int, int, int, list[str]]:
        """
        Download bookmarked/favorited videos from a URL list file.

        TikTok API doesn't allow direct access to bookmarks,
        so user must export URLs using browser console script.

        Returns:
            (successful, failed, skipped, failed_urls)
        """
        return self.bulk_download_from_file(urls_file, progress_callback)

    def parse_tiktok_data_export(self, file_path: str | Path) -> dict:
        """
        Parse TikTok's official data export file (ZIP or JSON).
        
        TikTok allows users to download their data from the app:
        Settings > Account > Download your data > Request data (JSON format)
        
        Args:
            file_path: Path to the ZIP or JSON file
            
        Returns:
            Dict with 'liked', 'favorites', 'watched' URL lists
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"TikTok data export dosyası bulunamadı: {file_path}")
        
        result = {
            "liked": [],
            "favorites": [],
            "watched": [],
        }
        
        # Handle ZIP file
        if file_path.suffix.lower() == ".zip":
            result = self._parse_tiktok_zip(file_path)
        # Handle JSON file
        elif file_path.suffix.lower() == ".json":
            result = self._parse_tiktok_json(file_path)
        else:
            # Try to detect format from content
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read(100)
                    if content.strip().startswith("{") or content.strip().startswith("["):
                        result = self._parse_tiktok_json(file_path)
                    else:
                        raise ValueError("Desteklenmeyen dosya formatı. ZIP veya JSON dosyası bekleniyor.")
            except (UnicodeDecodeError, IOError):
                # Might be a binary ZIP file with wrong extension
                try:
                    result = self._parse_tiktok_zip(file_path)
                except zipfile.BadZipFile:
                    raise ValueError("Desteklenmeyen dosya formatı. ZIP veya JSON dosyası bekleniyor.")
        
        return result
    
    def _parse_tiktok_zip(self, zip_path: Path) -> dict:
        """Parse TikTok data export ZIP file."""
        result = {"liked": [], "favorites": [], "watched": []}
        
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Look for relevant JSON files in the ZIP
            for name in zf.namelist():
                name_lower = name.lower()
                
                # Liked videos
                if "like" in name_lower and name.endswith(".json"):
                    try:
                        with zf.open(name) as f:
                            data = json.loads(f.read().decode("utf-8"))
                            urls = self._extract_urls_from_json(data, "liked")
                            result["liked"].extend(urls)
                    except (json.JSONDecodeError, KeyError):
                        continue
                
                # Favorites/Bookmarks
                if ("favorite" in name_lower or "bookmark" in name_lower) and name.endswith(".json"):
                    try:
                        with zf.open(name) as f:
                            data = json.loads(f.read().decode("utf-8"))
                            urls = self._extract_urls_from_json(data, "favorites")
                            result["favorites"].extend(urls)
                    except (json.JSONDecodeError, KeyError):
                        continue
                
                # Watch history (optional)
                if "watch" in name_lower and "history" in name_lower and name.endswith(".json"):
                    try:
                        with zf.open(name) as f:
                            data = json.loads(f.read().decode("utf-8"))
                            urls = self._extract_urls_from_json(data, "watched")
                            result["watched"].extend(urls)
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        return result
    
    def _parse_tiktok_json(self, json_path: Path) -> dict:
        """Parse a single TikTok JSON data file."""
        result = {"liked": [], "favorites": [], "watched": []}
        
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # TikTok exports can have different structures
        # Try to find video URLs in various locations
        
        # Structure 1: Direct list of items
        if isinstance(data, list):
            urls = self._extract_urls_from_list(data)
            result["liked"] = urls  # Default to liked if structure unclear
            
        # Structure 2: Nested object with Activity section
        elif isinstance(data, dict):
            # Check for "Activity" section (common in TikTok exports)
            activity = data.get("Activity", data)
            
            # Like List
            like_list = activity.get("Like List", {}).get("ItemFavoriteList", [])
            if not like_list:
                like_list = activity.get("LikeList", [])
            if not like_list:
                like_list = activity.get("Liked Videos", [])
            result["liked"] = self._extract_urls_from_list(like_list)
            
            # Favorites/Bookmarks
            fav_list = activity.get("Favorite Videos", {}).get("FavoriteVideoList", [])
            if not fav_list:
                fav_list = activity.get("Favorites", [])
            if not fav_list:
                fav_list = activity.get("Bookmarks", [])
            result["favorites"] = self._extract_urls_from_list(fav_list)
            
            # Watch History
            watch_list = activity.get("Video Browsing History", {}).get("VideoList", [])
            if not watch_list:
                watch_list = activity.get("WatchHistory", [])
            result["watched"] = self._extract_urls_from_list(watch_list)
        
        return result
    
    def _extract_urls_from_list(self, items: list) -> list[str]:
        """Extract TikTok URLs from a list of items."""
        urls = []
        
        for item in items:
            url = None
            
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
                    url = item["video"].get("url") or item["video"].get("link")
            
            if url and "tiktok.com" in url:
                # Clean URL (remove query params)
                clean_url = url.split("?")[0]
                if clean_url not in urls:
                    urls.append(clean_url)
        
        return urls
    
    def _extract_urls_from_json(self, data: dict | list, category: str) -> list[str]:
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
        file_path: str | Path,
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
        data = self.parse_tiktok_data_export(file_path)
        return data.get(category, [])

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
            from http.cookiejar import MozillaCookieJar
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

        except (OSError, IOError, ValueError) as e:
            return False, f"Cookie dosyası okunamadı: {e}"

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
