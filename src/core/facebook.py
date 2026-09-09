"""
Facebook Video Downloader Module
Uses multiple methods (Selenium, yt-dlp) for reliable Facebook downloads.
Supports single and bulk downloads with cookie authentication.
"""

import atexit
import os
import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import requests
import yt_dlp

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from rich.console import Console

from src.core.base import (
    DownloaderBase,
    DownloadError,
)
from src.utils.history import DownloadHistory

console = Console()


class FacebookDownloader(DownloaderBase):
    """Facebook video downloader with multiple download methods."""

    def __init__(self, config: Any):
        super().__init__(config)
        self.facebook_path = self.config.facebook_path
        self.driver = None
        
        os.makedirs(self.facebook_path, exist_ok=True)
        atexit.register(self.close_selenium)
        self.history = DownloadHistory(
            config.download_path,
            platform_paths={"facebook": Path(self.facebook_path)}
        )

    def _load_cookies_to_session(self) -> requests.Session:
        """Load Netscape format cookies to requests session."""
        session = requests.Session()
        session.headers.update(self.default_headers)
        
        if self.config.facebook_cookies_file:
            from http.cookiejar import MozillaCookieJar
            jar = MozillaCookieJar(self.config.facebook_cookies_file)
            jar.load(ignore_discard=True, ignore_expires=True)
            session.cookies.update(jar)
            
        return session

    def _parse_cookies_for_selenium(self) -> list[dict]:
        """Convert cookie file to Selenium format."""
        if not self.config.facebook_cookies_file:
            return []
            
        cookies = []
        try:
            with open(self.config.facebook_cookies_file, 'r') as f:
                for line in f:
                    if not line.startswith('#') and line.strip():
                        parts = line.strip().split('\t')
                        if len(parts) >= 7:
                            cookie = {
                                'domain': parts[0],
                                'name': parts[5],
                                'value': parts[6],
                                'path': parts[2],
                                'secure': parts[3] == 'TRUE',
                                'expiry': int(parts[4]) if parts[4].isdigit() else None
                            }
                            cookies.append(cookie)
        except Exception:
            pass
        return cookies

    def _init_selenium(self) -> None:
        """Initialize Selenium WebDriver."""
        if not SELENIUM_AVAILABLE:
            raise DownloadError("Selenium kütüphanesi yüklü değil!")
            
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"user-agent={self.default_headers['User-Agent']}")
        
        try:
            # Try native Selenium 4 Manager first (no webdriver-manager download needed)
            self.driver = webdriver.Chrome(options=options)
        except Exception:
            try:
                # Fallback to ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                raise DownloadError(f"WebDriver hatası: {e}")

    def _load_cookies_to_selenium(self) -> None:
        """Load cookies to Selenium."""
        if not self.driver or not self.config.facebook_cookies_file:
            return
            
        # Selenium needs to be on the domain to set cookies
        self.driver.get("https://www.facebook.com")
        time.sleep(2)
        
        cookies = self._parse_cookies_for_selenium()
        for cookie in cookies:
            try:
                # Filter cookies only for facebook domain to avoid errors
                if 'facebook.com' in cookie['domain']:
                    # Remove expiry if it's too far in the future or null
                    if 'expiry' in cookie:
                        del cookie['expiry']
                    self.driver.add_cookie(cookie)
            except Exception:
                continue
                
        self.driver.refresh()
        time.sleep(2)

    def _method_selenium(self, url: str) -> tuple[bool, str]:
        """Method 1: Download video using Selenium (most effective)."""
        if not SELENIUM_AVAILABLE:
            return False, "Selenium yüklü değil"
            
        try:
            if not self.driver:
                self._init_selenium()
                self._load_cookies_to_selenium()
            
            self.driver.get(url)
            time.sleep(5) # Wait for page to load and JS to execute
            
            # Look for video URL in page source using regex patterns
            # Pattern 1: browser_native_sd_url / browser_native_hd_url
            source = self.driver.page_source
            
            video_url = None
            
            # Try to find HD URL first
            hd_match = re.search(r'browser_native_hd_url":"([^"]+)"', source)
            if hd_match:
                video_url = hd_match.group(1).replace('\\/', '/')
            else:
                sd_match = re.search(r'browser_native_sd_url":"([^"]+)"', source)
                if sd_match:
                    video_url = sd_match.group(1).replace('\\/', '/')
            
            if not video_url:
                # Try pattern 2: videoData
                vd_match = re.search(r'"videoData":\[{"hl":"([^"]+)"', source)
                if vd_match:
                    video_url = vd_match.group(1).replace('\\/', '/')

            if video_url:
                video_id = self._extract_video_id(url) or str(int(time.time()))
                return self._download_video_direct(video_url, video_id, original_url=url)
            
            return False, "Video kaynağı bulunamadı"
            
        except Exception as e:
            return False, f"Selenium hatası: {e}"

    def close_selenium(self) -> None:
        """Close Selenium WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    def validate_facebook_cookies(self, cookie_file: str) -> tuple[bool, str]:
        """Validate Facebook cookie file."""
        if not os.path.exists(cookie_file):
            return False, "Dosya bulunamadı"
            
        # Basic check for facebook specific cookies
        try:
            with open(cookie_file, 'r') as f:
                content = f.read()
                if 'c_user' in content and 'xs' in content:
                    self.config.facebook_cookies_file = cookie_file
                    return True, ""
                return False, "Geçersiz Facebook cookie dosyası"
        except Exception as e:
            return False, f"Okuma hatası: {e}"

    def _extract_video_id(self, url: str) -> str | None:
        """Extract video ID from URL."""
        # /videos/12345/ or /watch/?v=12345 or /reel/12345
        patterns = [
            r"videos/(\d+)",
            r"v=(\d+)",
            r"reel/(\d+)"
        ]
        for p in patterns:
            match = re.search(p, url)
            if match:
                return match.group(1)
        return None

    def _download_video_direct(
        self,
        video_url: str,
        video_id: str,
        original_url: str | None = None
    ) -> tuple[bool, str]:
        """Download video directly from URL."""
        filename = f"facebook_{video_id}.mp4"
        filepath = os.path.join(self.facebook_path, filename)
        
        try:
            with self._load_cookies_to_session() as session:
                with session.get(video_url, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(filepath, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=65536):
                            if chunk:
                                f.write(chunk)
            
            history_url = original_url if original_url else video_url
            self.history.add_download(history_url, "facebook")
            return True, f"Başarıyla indirildi: {filename}"
        except Exception as e:
            return False, f"İndirme hatası: {e}"

    def _method_ytdlp(self, url: str) -> tuple[bool, str]:
        """Download using yt-dlp."""
        ydl_opts = self.get_base_options()
        ydl_opts.update({
            "outtmpl": os.path.join(self.facebook_path, "fb_%(id)s.%(ext)s"),
            "cookiefile": self.config.facebook_cookies_file if self.config.facebook_cookies_file else None,
        })
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                error_code = ydl.download([url])
                if error_code == 0:
                    self.history.add_download(url, "facebook")
                    return True, "yt-dlp ile başarıyla indirildi"
                return False, "yt-dlp başarısız oldu"
        except Exception as e:
            return False, f"yt-dlp hatası: {e}"

    def download(
        self,
        url: str,
        progress_hooks: list[Callable] | None = None,
        skip_duplicate_check: bool = False
    ) -> tuple[bool, str]:
        """Main download function that tries all methods in sequence."""
        if not skip_duplicate_check:
            is_dup, dup_date = self.history.is_downloaded(url, "facebook")
            if is_dup:
                return False, f"Zaten indirilmiş ({dup_date})"

        # Try Method 1: yt-dlp first (it's faster if it works)
        success, msg = self._method_ytdlp(url)
        if success:
            return True, msg
            
        # Try Method 2: Selenium
        if SELENIUM_AVAILABLE:
            success, msg = self._method_selenium(url)
            if success:
                return True, msg
        
        return False, f"Hiçbir yöntemle indirilemedi: {msg}"

    def download_bulk(
        self,
        file_path: str,
        progress_callback: Callable[[int, int, str, bool, str], None] | None = None
    ) -> tuple[int, int, int, list[str]]:
        """Bulk download from file."""
        if not os.path.exists(file_path):
            return 0, 0, 0, []
            
        try:
            with open(file_path, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
        except OSError:
            return 0, 0, 0, []
            
        successful = 0
        failed = 0
        skipped = 0
        failed_urls: list[str] = []
        
        total = len(urls)
        
        for i, url in enumerate(urls):
            if progress_callback:
                progress_callback(i + 1, total, url, True, "İndiriliyor...")
            
            # Duplicate check
            is_dup, dup_date = self.history.is_downloaded(url, "facebook")
            if is_dup:
                skipped += 1
                if progress_callback:
                    progress_callback(i + 1, total, url, True, f"Atlandı ({dup_date})")
                continue
                
            success, msg = self.download(url, skip_duplicate_check=True)
            
            if success:
                successful += 1
            else:
                failed += 1
                failed_urls.append(f"{url} | {msg}")
        
        # Batch save history
        self.history.save_history()

        # Close Selenium
        self.close_selenium()
                
        return successful, failed, skipped, failed_urls

    def get_url_extraction_script(self) -> str:
        """
        Return JavaScript code for extracting Facebook video URLs.
        User should run this in browser console on their saved videos page.
        """
        return '''
// Facebook Saved Video URL Extractor
// 1. Go to your saved videos page on Facebook
// 2. Scroll down to load all videos you want
// 3. Open browser console (F12 -> Console)
// 4. Paste and run this script
// 5. Copy the result and save to a .txt file

(function() {
    const videoLinks = new Set();
    
    // Find all video links on the page (common patterns)
    document.querySelectorAll('a[href*="/videos/"], a[href*="/watch/"], a[href*="/reel/"]').forEach(a => {
        const href = a.href;
        if (href.includes('facebook.com')) {
            // Extract numeric ID to build a clean link
            const match = href.match(/\\/(?:videos|reel|watch)\\/?(?:\\?v=)?(\\d+)/);
            if (match) {
                videoLinks.add(`https://www.facebook.com/watch/?v=${match[1]}`);
            }
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
