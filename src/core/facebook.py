import os
import re
import json
import time
import requests
import yt_dlp
from pathlib import Path
from rich.console import Console
from urllib.parse import unquote

console = Console()

class FacebookDownloader:
    def __init__(self, config):
        self.config = config
        self.facebook_path = self.config.facebook_path
        self.driver = None
        
        # Klasör oluştur
        if not self.facebook_path.exists():
            self.facebook_path.mkdir(parents=True, exist_ok=True)
        
        # Session oluştur (cookie desteği için)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        
        # Cookie'leri yükle
        self._load_cookies_to_session()

    def _load_cookies_to_session(self):
        """Netscape formatındaki cookie dosyasını requests session'a yükle."""
        if not self.config.facebook_cookies_file:
            return
        
        try:
            with open(self.config.facebook_cookies_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split('\t')
                    if len(parts) >= 7:
                        domain, _, path, secure, expires, name, value = parts[:7]
                        if 'facebook.com' in domain:
                            self.session.cookies.set(name, value, domain=domain, path=path)
        except Exception as e:
            console.print(f"[dim]Cookie yükleme hatası: {e}[/dim]")

    def _parse_cookies_for_selenium(self):
        """Cookie dosyasını Selenium formatına çevir."""
        cookies = []
        if not self.config.facebook_cookies_file:
            return cookies
        
        try:
            with open(self.config.facebook_cookies_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split('\t')
                    if len(parts) >= 7:
                        domain, _, path, secure, expires, name, value = parts[:7]
                        if 'facebook.com' in domain:
                            cookie = {
                                'name': name,
                                'value': value,
                                'domain': domain if domain.startswith('.') else f'.{domain}',
                                'path': path,
                                'secure': secure.upper() == 'TRUE',
                            }
                            # Expiry ekle (0 veya boş değilse)
                            try:
                                exp = int(expires)
                                if exp > 0:
                                    cookie['expiry'] = exp
                            except:
                                pass
                            cookies.append(cookie)
        except Exception as e:
            console.print(f"[dim]Cookie parse hatası: {e}[/dim]")
        
        return cookies

    def _init_selenium(self):
        """Selenium WebDriver'ı başlat."""
        if self.driver:
            return True
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager
            
            options = Options()
            options.add_argument('--headless=new')  # Arka planda çalış
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)
            
            # ChromeDriver otomatik indir
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Bot tespitini atla
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                '''
            })
            
            return True
            
        except Exception as e:
            console.print(f"[red]Selenium başlatma hatası: {e}[/red]")
            return False

    def _load_cookies_to_selenium(self):
        """Cookie'leri Selenium'a yükle."""
        if not self.driver:
            return False
        
        # Önce facebook.com'a git (cookie domain eşleşmesi için)
        self.driver.get('https://www.facebook.com')
        time.sleep(2)
        
        cookies = self._parse_cookies_for_selenium()
        loaded = 0
        
        for cookie in cookies:
            try:
                self.driver.add_cookie(cookie)
                loaded += 1
            except Exception as e:
                pass  # Bazı cookie'ler eklenemeyebilir
        
        console.print(f"[dim]Selenium'a {loaded} cookie yüklendi[/dim]")
        
        # Sayfayı yenile
        self.driver.refresh()
        time.sleep(2)
        
        return loaded > 0

    def _method_selenium(self, url):
        """Yöntem 1: Selenium ile video indirme (En etkili)."""
        try:
            # Selenium'u başlat
            if not self._init_selenium():
                return False, "Selenium başlatılamadı"
            
            # Cookie'leri yükle (ilk seferde)
            if not hasattr(self, '_selenium_cookies_loaded'):
                self._load_cookies_to_selenium()
                self._selenium_cookies_loaded = True
            
            # Video sayfasına git
            console.print(f"[dim]Selenium: {url} yükleniyor...[/dim]")
            self.driver.get(url)
            
            # Sayfa yüklenmesini bekle
            time.sleep(3)
            
            # Scroll yaparak video yüklemesini tetikle
            try:
                self.driver.execute_script("window.scrollTo(0, 300);")
                time.sleep(1)
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)
            except:
                pass
            
            # Video URL'sini bulmak için birden fazla deneme
            video_url = None
            
            for attempt in range(3):
                page_source = self.driver.page_source
                
                # Video URL pattern'leri (öncelik sırasına göre)
                patterns = [
                    # HD kalite
                    r'"hd_src":"([^"]+)"',
                    r'"playable_url_quality_hd":"([^"]+)"',
                    r'"browser_native_hd_url":"([^"]+)"',
                    # SD kalite
                    r'"sd_src":"([^"]+)"',
                    r'"playable_url":"([^"]+)"',
                    r'"browser_native_sd_url":"([^"]+)"',
                    # Alternatif formatlar
                    r'"videoUri":"([^"]+)"',
                    r'"src":"(https://[^"]+\.mp4[^"]*)"',
                    r'<source[^>]+src="([^"]+\.mp4[^"]*)"',
                    # Facebook CDN linkleri
                    r'(https://video[^"]+\.fbcdn\.net/[^"]+\.mp4[^"]*)',
                    r'(https://scontent[^"]+\.fbcdn\.net/[^"]+\.mp4[^"]*)',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, page_source)
                    for match in matches:
                        candidate = match
                        # URL temizle
                        candidate = candidate.replace('\\/', '/')
                        candidate = candidate.replace('\\u0025', '%')
                        candidate = candidate.replace('\\u003C', '<')
                        candidate = candidate.replace('\\u003E', '>')
                        candidate = candidate.replace('\\"', '"')
                        candidate = candidate.replace('\\\\', '\\')
                        
                        try:
                            candidate = candidate.encode().decode('unicode_escape')
                        except:
                            pass
                        
                        # Geçerli bir video URL'si mi kontrol et
                        if candidate and 'mp4' in candidate.lower() and 'http' in candidate.lower():
                            video_url = candidate
                            break
                    
                    if video_url:
                        break
                
                if video_url:
                    break
                
                # Video bulunamadı, biraz bekle ve tekrar dene
                if attempt < 2:
                    console.print(f"[dim]Video bulunamadı, tekrar deneniyor ({attempt + 2}/3)...[/dim]")
                    time.sleep(3)
                    # Sayfayı yenile
                    self.driver.refresh()
                    time.sleep(3)
            
            # JavaScript ile de dene
            if not video_url:
                try:
                    # Video elementlerinden src al
                    videos = self.driver.find_elements("css selector", "video")
                    for video_el in videos:
                        src = video_el.get_attribute('src')
                        if src and 'blob:' not in src and 'mp4' in src:
                            video_url = src
                            break
                        # data-src veya currentSrc dene
                        src = video_el.get_attribute('currentSrc')
                        if src and 'blob:' not in src:
                            video_url = src
                            break
                except:
                    pass
            
            if video_url:
                console.print(f"[green]Video URL bulundu![/green]")
                # Video'yu indir
                video_id = self._extract_video_id(url) or str(int(time.time()))
                return self._download_video_direct(video_url, video_id)
            
            return False, "Selenium: Video URL bulunamadı"
            
        except Exception as e:
            return False, f"Selenium hatası: {str(e)}"

    def close_selenium(self):
        """Selenium'u kapat."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

    def validate_facebook_cookies(self, cookie_file):
        """Facebook cookie dosyasını kontrol et."""
        try:
            with open(cookie_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                has_c_user = 'c_user' in content
                has_xs = 'xs' in content
                is_fb_domain = '.facebook.com' in content
                
                if (has_c_user and has_xs) or (is_fb_domain and 'facebook.com' in content):
                    return True, "Facebook çerezleri bulundu"
                else:
                    return False, "Dosyada Facebook giriş bilgileri (c_user, xs) bulunamadı."
        except Exception as e:
            return False, str(e)

    def _extract_video_id(self, url):
        """URL'den video ID'sini çıkar."""
        patterns = [
            r'/videos/(\d+)',
            r'/watch/?\?v=(\d+)',
            r'/reel/(\d+)',
            r'story_fbid=(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def _download_video_direct(self, video_url, video_id):
        """Doğrudan video URL'sinden indir."""
        try:
            filename = self.facebook_path / f"Facebook_Video_{video_id}.mp4"
            
            # Zaten varsa atla
            if filename.exists():
                return True, f"Zaten indirilmiş: {filename.name}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.facebook.com/',
            }
            
            response = requests.get(video_url, headers=headers, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return True, f"İndirildi: {filename.name}"
            
        except Exception as e:
            return False, str(e)

    def _method_ytdlp(self, url):
        """yt-dlp ile indirme."""
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': str(self.facebook_path / '%(title).100s [%(id)s].%(ext)s'),
            'ignoreerrors': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

        if self.config.facebook_cookies_file:
            ydl_opts['cookiefile'] = self.config.facebook_cookies_file

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info:
                    title = info.get('title', 'Facebook Video')
                    return True, f"İndirildi: {title}"
                return False, "Video bilgisi alınamadı"
        except Exception as e:
            return False, str(e)

    def download(self, url):
        """Tüm yöntemleri sırayla deneyen ana indirme fonksiyonu."""
        if not url:
            return False, "URL boş."
        
        # Geçersiz linkleri filtrele
        if "facebook.com/reel/?s=" in url or "facebook.com/reel?s=" in url:
            return False, "Geçersiz link (genel reel sayfası)"
        
        video_id = self._extract_video_id(url)
        
        # Zaten indirilmiş mi kontrol et
        if video_id:
            existing = list(self.facebook_path.glob(f"*{video_id}*"))
            if existing:
                return True, f"Zaten indirilmiş: {existing[0].name}"
        
        # ═══════════════════════════════════════════════════════════════
        # YÖNTEM 1: Selenium (En etkili, grup videoları için)
        # ═══════════════════════════════════════════════════════════════
        console.print("[cyan]▶ Yöntem 1: Selenium deneniyor...[/cyan]")
        success, msg = self._method_selenium(url)
        if success:
            return True, msg
        
        # ═══════════════════════════════════════════════════════════════
        # YÖNTEM 2: yt-dlp (Fallback)
        # ═══════════════════════════════════════════════════════════════
        console.print("[cyan]▶ Yöntem 2: yt-dlp deneniyor...[/cyan]")
        success, msg = self._method_ytdlp(url)
        if success:
            return True, msg
        
        # Watch formatını da dene
        if video_id and "watch/?v=" not in url:
            watch_url = f"https://www.facebook.com/watch/?v={video_id}"
            success, msg = self._method_ytdlp(watch_url)
            if success:
                return True, msg
        
        return False, f"Tüm yöntemler başarısız. Son hata: {msg}"

    def download_bulk(self, file_path, progress_callback=None):
        """Dosyadan toplu indirme yap."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
        except Exception as e:
            return 0, 0, [], 0
            
        successful = 0
        failed = 0
        skipped = 0
        failed_urls = []
        
        total = len(urls)
        
        for i, url in enumerate(urls):
            if progress_callback:
                progress_callback(i + 1, total, url, True, "İndiriliyor...")
                
            success, msg = self.download(url)
            
            if success:
                successful += 1
            else:
                failed += 1
                failed_urls.append(f"{url} | {msg}")
        
        # Selenium'u kapat
        self.close_selenium()
                
        return successful, failed, failed_urls, skipped
