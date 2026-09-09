"""
Account Controller
Handles user authentication and cookie management.
"""

import os

from src.controllers.base import BaseController
from src.core.auth import AuthManager
from src.core.facebook import FacebookDownloader
from src.core.tiktok import TikTokDownloader
from src.core.twitter import TwitterDownloader
from src.core.youtube import YoutubeDownloader


class AccountController(BaseController):
    """Controller for account and cookie management."""
    
    def __init__(self, config, ui):
        super().__init__(config, ui)
        # Auth manager for YouTube authentication
        self.auth_manager = AuthManager(config)
        # Downloaders to validate cookies
        self.yt_downloader = YoutubeDownloader(config)
        self.tw_downloader = TwitterDownloader(config)
        self.tt_downloader = TikTokDownloader(config)
        self.fb_downloader = FacebookDownloader(config)
    
    def run(self) -> None:
        """Account menu loop."""
        self.ui.push_breadcrumb("Hesap İşlemleri")
        
        while True:
            self.ui.print_header(self.config.download_path)
            
            import questionary
            choices = [
                "⚡ İndirilenler Klasörünü Tara ve Otomatik Bağla (TEK TIK)",
                "Tek Cookie Dosyası ile Tümünü Bağla (Seçimli)",
                "YouTube Bağlantısı (Cookies/Browser)",
                "Twitter Bağlantısı (Cookies)",
                "TikTok Bağlantısı (Cookies)",
                "Facebook Bağlantısı (Cookies)",
                "Geri Dön"
            ]
            
            choice = questionary.select(
                "Hesap ve Bağlantı Ayarları:",
                choices=choices,
                style=self.ui.custom_style
            ).ask()
            
            if not choice or "Geri Dön" in choice:
                break
            
            if "Otomatik Tara" in choice:
                self.handle_auto_scan_and_connect()
            elif "Tek Cookie" in choice:
                self.handle_universal_auth()
            elif "YouTube" in choice:
                self.handle_youtube_auth()
            elif "Twitter" in choice:
                self.handle_twitter_auth()
            elif "TikTok" in choice:
                self.handle_tiktok_auth()
            elif "Facebook" in choice:
                self.handle_facebook_auth()
                
        self.ui.pop_breadcrumb()

    def handle_auto_scan_and_connect(self) -> None:
        """Automatically scan Downloads for the most recent cookie file and bind all platforms."""
        self.ui.console.print("\n[bold cyan]⚡ İndirilenler klasörü taranıyor...[/bold cyan]\n")
        detected = self.find_cookie_files()
        
        if not detected:
            self.ui.show_error("İndirilenler klasöründe cookie dosyası (*cookie*.txt) bulunamadı!")
            self.ui.console.print("[dim]Tarayıcınızdan 'Get cookies.txt LOCALLY' eklentisiyle çerezleri indirdiğinizden (.txt) emin olun.[/dim]")
            self.ui.wait_for_enter()
            return
            
        best_file = str(detected[0])
        self.ui.console.print(f"[green]✓ En güncel cookie dosyası tespit edildi:[/green] [bold white]{detected[0].name}[/bold white]")
        self.ui.console.print(f"[dim]Konum: {best_file}[/dim]\n")
        
        self._apply_universal_cookies(best_file)

    def handle_universal_auth(self) -> None:
        """Handle setting a single cookie file for all platforms."""
        self.ui.console.print("\n[bold yellow]Bu mod tek bir Netscape formatındaki cookie dosyasını tüm platformlar için kullanır.[/bold yellow]\n")
        
        file_path = self.prompt_cookie_file(platform_name="Tüm Platformlar")
        if not file_path:
            return
            
        if not os.path.exists(file_path):
            self.ui.show_error("Dosya bulunamadı!")
            self.ui.wait_for_enter()
            return

        self._apply_universal_cookies(file_path)

    def _apply_universal_cookies(self, file_path: str) -> None:
        """Validate and apply a cookie file to all platforms."""
        results = []
        
        # 1. YouTube
        if self.auth_manager.validate_cookies_file(file_path):
            ch_name = f" ({self.config.channel_name})" if self.config.channel_name else ""
            results.append(f"[green]✓ YouTube{ch_name}[/green]")
        else:
            self.config.auth_method = "cookies_file"
            self.config.cookies_file = file_path
            results.append("[green]✓ YouTube (Kaydedildi)[/green]")
        
        # 2. Twitter Validate
        success, msg = self.tw_downloader.validate_twitter_cookies(file_path)
        if success:
            self.config.twitter_cookies_file = file_path
            results.append("[green]✓ Twitter/X[/green]")
        else:
            results.append(f"[red]✗ Twitter ({msg})[/red]")

        # 3. TikTok Validate
        success, msg = self.tt_downloader.validate_tiktok_cookies(file_path)
        if success:
            self.config.tiktok_cookies_file = file_path
            results.append("[green]✓ TikTok[/green]")
        else:
            results.append(f"[red]✗ TikTok ({msg})[/red]")

        # 4. Facebook Validate
        success, msg = self.fb_downloader.validate_facebook_cookies(file_path)
        if success:
            self.config.facebook_cookies_file = file_path
            results.append("[green]✓ Facebook[/green]")
        else:
            results.append(f"[red]✗ Facebook ({msg})[/red]")

        # Save and Report
        self.config.save()
        
        self.ui.console.print("\n[bold cyan]Bağlantı Sonuçları:[/bold cyan]")
        for res in results:
            self.ui.console.print(res)
            
        self.ui.wait_for_enter()


    def handle_youtube_auth(self) -> None:
        """Handle YouTube authentication settings."""
        import questionary
        method = questionary.select(
            "YouTube doğrulama yöntemi:",
            choices=["Browser tıkla (Chrome/Edge/Firefox)", "Cookies Dosyası (.txt)", "Giriş Yapılmasın"],
            style=self.ui.custom_style
        ).ask()
        
        if not method or "Giriş Yapılmasın" in method:
            self.config.auth_method = None
            self.config.save()
            return

        if "Browser" in method:
            browser = questionary.select(
                "Hangi tarayıcı kullanılacak?",
                choices=["chrome", "firefox", "edge", "safari", "opera"],
                style=self.ui.custom_style
            ).ask()
            if browser:
                valid = self.auth_manager.validate_browser_cookies(browser)
                if valid:
                    self.config.save()
                    ch = f" ({self.config.channel_name})" if self.config.channel_name else ""
                    self.ui.show_success(f"YouTube için {browser} tarayıcısı başarıyla bağlandı{ch}!")
                else:
                    self.config.auth_method = "browser"
                    self.config.browser = browser
                    self.config.save()
                    self.ui.show_warning(f"{browser} tarayıcısından aktif YouTube oturumu bulunamadı, ancak ayar kaydedildi.")
        
        else:
            file_path = self.prompt_cookie_file(platform_name="YouTube", keyword="youtube")
            if not file_path:
                return
            if not os.path.exists(file_path):
                self.ui.show_error("Dosya bulunamadı!")
                self.ui.wait_for_enter()
                return

            valid = self.auth_manager.validate_cookies_file(file_path)
            if valid:
                self.config.save()
                ch = f" ({self.config.channel_name})" if self.config.channel_name else ""
                self.ui.show_success(f"YouTube cookie dosyası doğrulandı{ch}!")
            else:
                self.config.auth_method = "cookies_file"
                self.config.cookies_file = file_path
                self.config.save()
                self.ui.show_success("YouTube cookie dosyası kaydedildi.")
        
        self.ui.wait_for_enter()

    def handle_twitter_auth(self) -> None:
        """Handle Twitter authentication via cookies."""
        import questionary
        file_path = self.prompt_cookie_file(platform_name="Twitter/X", keyword="twitter")
        if not file_path:
            return
            
        if not os.path.exists(file_path):
            self.ui.show_error("Dosya bulunamadı!")
            self.ui.wait_for_enter()
            return
            
        success, msg = self.tw_downloader.validate_twitter_cookies(file_path)
        if success:
            self.config.twitter_cookies_file = file_path
            username = questionary.text("Twitter Kullanıcı Adınız (Opsiyonel):", style=self.ui.custom_style).ask()
            self.config.twitter_username = username
            self.config.save()
            self.ui.show_success("Twitter bağlantısı başarılı!")
            self.logger.auth_event("twitter", True, "cookies")
        else:
            self.ui.show_error(f"Hata: {msg}")
            self.logger.auth_event("twitter", False, "cookies")
            
        self.ui.wait_for_enter()

    def handle_tiktok_auth(self) -> None:
        """Handle TikTok authentication via cookies."""
        import questionary
        file_path = self.prompt_cookie_file(platform_name="TikTok", keyword="tiktok")
        if not file_path:
            return
            
        if not os.path.exists(file_path):
            self.ui.show_error("Dosya bulunamadı!")
            self.ui.wait_for_enter()
            return
            
        success, msg = self.tt_downloader.validate_tiktok_cookies(file_path)
        if success:
            self.config.tiktok_cookies_file = file_path
            username = questionary.text("TikTok Kullanıcı Adınız (Opsiyonel):", style=self.ui.custom_style).ask()
            self.config.tiktok_username = username
            self.config.save()
            self.ui.show_success("TikTok bağlantısı başarılı!")
            self.logger.auth_event("tiktok", True, "cookies")
        else:
            self.ui.show_error(f"Hata: {msg}")
            self.logger.auth_event("tiktok", False, "cookies")
            
        self.ui.wait_for_enter()

    def handle_facebook_auth(self) -> None:
        """Handle Facebook authentication via cookies."""
        file_path = self.prompt_cookie_file(platform_name="Facebook", keyword="facebook")
        if not file_path:
            return
            
        if not os.path.exists(file_path):
            self.ui.show_error("Dosya bulunamadı!")
            self.ui.wait_for_enter()
            return
            
        success, msg = self.fb_downloader.validate_facebook_cookies(file_path)
        if success:
            self.config.facebook_cookies_file = file_path
            self.config.save()
            self.ui.show_success("Facebook bağlantısı başarılı!")
            self.logger.auth_event("facebook", True, "cookies")
        else:
            self.ui.show_error(f"Hata: {msg}")
            self.logger.auth_event("facebook", False, "cookies")
            
        self.ui.wait_for_enter()

