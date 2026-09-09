import os

import yt_dlp
from rich.console import Console


class AuthManager:
    def __init__(self, config):
        self.config = config
        self.console = Console()

    def get_channel_name_from_cookies_file(self, cookies_file):
        """
        Cookie dosyası kullanarak giriş yapan kullanıcının kanal adını alır.
        """
        url = "https://www.youtube.com/playlist?list=LL"

        ydl_opts = {
            "cookiefile": cookies_file,
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "ignoreerrors": True,
            "extractor_args": {"youtubetab": {"skip": ["authcheck"]}},
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    channel_name = (
                        info.get("channel")
                        or info.get("uploader")
                        or info.get("uploader_id")
                    )
                    return channel_name
        except Exception:
            pass
        return None

    def validate_cookies_file(self, cookies_file):
        """
        Cookie dosyasının geçerli olup olmadığını test eder.
        """
        if not os.path.exists(cookies_file):
            self.console.print(f"[red]Dosya bulunamadı: {cookies_file}[/red]")
            return False

        self.console.print(
            "[yellow]Cookie dosyası kontrol ediliyor...[/yellow]"
        )

        url = "https://www.youtube.com/feed/playlists"

        ydl_opts = {
            "cookiefile": cookies_file,
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "ignoreerrors": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if info and ("entries" in info or info.get("title")):
                    self.config.auth_method = "cookies_file"
                    self.config.cookies_file = cookies_file
                    self.config.browser = None
                    self.config.channel_name = self.get_channel_name_from_cookies_file(cookies_file)
                    return True
                else:
                    return False
        except Exception as e:
            self.console.print(f"[dim]Hata: {e}[/dim]")
            return False

    def get_channel_name(self, browser_name):
        """
        Giriş yapan kullanıcının kanal adını alır.
        Beğenilen Videolar playlist'inden kullanıcı adını çeker.
        """
        # Beğenilen Videolar playlist'i - giriş yapan kullanıcının adını içerir
        url = "https://www.youtube.com/playlist?list=LL"

        ydl_opts = {
            "cookiesfrombrowser": (browser_name,),
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "ignoreerrors": True,
            "extractor_args": {"youtubetab": {"skip": ["authcheck"]}},
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    # Kanal adını al - "channel" veya "uploader" alanından
                    channel_name = (
                        info.get("channel")
                        or info.get("uploader")
                        or info.get("uploader_id")
                    )
                    return channel_name
        except Exception:
            pass
        return None

    def validate_browser_cookies(self, browser_name):
        """
        Seçilen tarayıcının çerezlerinin çalışıp çalışmadığını test eder.
        Bunu yapmak için kullanıcının kütüphane sayfasına erişmeyi dener.
        """
        self.console.print(
            f"[yellow]{browser_name} çerezleri kontrol ediliyor...[/yellow]"
        )

        # Test URL'si: Sadece giriş yapmış kullanıcıların görebileceği bir sayfa
        # feed/playlists iyi bir adaydır.
        url = "https://www.youtube.com/feed/playlists"

        ydl_opts = {
            "cookiesfrombrowser": (browser_name,),
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,  # Hızlı kontrol için
            "ignoreerrors": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # Eğer giriş yapılmamışsa genellikle boş döner veya hata verir.
                # Giriş yapılmışsa 'entries' içinde veriler olur veya title 'Library' vb. olur.
                if info and ("entries" in info or info.get("title")):
                    self.config.auth_method = "browser"
                    self.config.browser = browser_name
                    # Kanal adını al
                    self.config.channel_name = self.get_channel_name(browser_name)
                    return True
                else:
                    return False
        except Exception:
            return False

    def logout(self):
        """Oturum bilgisini siler."""
        self.config.auth_method = None
        self.config.browser = None
        self.config.cookies_file = None
        self.config.channel_name = None
        return True

    def get_user_playlists(self):
        """
        Oturum açmış kullanıcının playlistlerini listeler.
        """
        if not self.config.auth_method:
            return []

        url = "https://www.youtube.com/feed/playlists"

        ydl_opts = {
            "extract_flat": True,
            "quiet": True,
            "ignoreerrors": True,
        }

        # Auth yöntemine göre cookie ekle
        if self.config.auth_method == "cookies_file" and self.config.cookies_file:
            ydl_opts["cookiefile"] = self.config.cookies_file
        elif self.config.auth_method == "browser" and self.config.browser:
            ydl_opts["cookiesfrombrowser"] = (self.config.browser,)
        else:
            return []

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info and "entries" in info:
                    playlists = []
                    for entry in info["entries"]:
                        if entry.get("title") and entry.get("url"):
                            playlists.append(entry)
                    return playlists
                return []
        except Exception:
            return []
