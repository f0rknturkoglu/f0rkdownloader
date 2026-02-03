"""
Account Controller
Handles user authentication and cookie management.
"""

import os
from pathlib import Path
from src.controllers.base import BaseController
from src.core.youtube import YoutubeDownloader
from src.core.twitter import TwitterDownloader
from src.core.tiktok import TikTokDownloader
from src.core.facebook import FacebookDownloader


class AccountController(BaseController):
    """Controller for account and cookie management."""
    
    def __init__(self, config, ui):
        super().__init__(config, ui)
        # We need downloaders to validate cookies
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
                "Tek Cookie Dosyası ile Tümünü Bağla (ÖNERİLEN)",
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
            
            if "Tek Cookie" in choice:
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

    def handle_universal_auth(self) -> None:
        """Handle setting a single cookie file for all platforms."""
        import questionary
        self.ui.console.print("\n[bold yellow]Bu mod tek bir Netscape formatındaki cookie dosyasını tüm platformlar için kullanır.[/bold yellow]\n")
        
        file_path = questionary.text("Cookie dosyası yolu (.txt):", style=self.ui.custom_style).ask()
        if not file_path or not os.path.exists(file_path):
            self.ui.show_error("Dosya bulunamadı!")
            return

        results = []
        
        # 1. YouTube
        self.config.auth_method = "cookies_file"
        self.config.cookies_file = file_path
        results.append("[green]✓ YouTube[/green]")
        
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
        
        self.ui.console.print("\n[bold cyan]Sonuçlar:[/bold cyan]")
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
                self.config.auth_method = "browser"
                self.config.browser = browser
                self.config.save()
                self.ui.show_success(f"YouTube için {browser} tarayıcısı seçildi.")
        
        else:
            file_path = questionary.text("Cookie dosyası yolu (.txt):", style=self.ui.custom_style).ask()
            if file_path and os.path.exists(file_path):
                self.config.auth_method = "cookies_file"
                self.config.cookies_file = file_path
                self.config.save()
                self.ui.show_success("YouTube cookie dosyası kaydedildi.")
            else:
                self.ui.show_error("Geçersiz dosya yolu.")
        
        self.ui.wait_for_enter()

    def handle_twitter_auth(self) -> None:
        """Handle Twitter authentication via cookies."""
        import questionary
        file_path = questionary.text("Twitter Cookie dosyası yolu (.txt):", style=self.ui.custom_style).ask()
        if not file_path:
            return
            
        success, msg = self.tw_downloader.validate_twitter_cookies(file_path)
        if success:
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
        file_path = questionary.text("TikTok Cookie dosyası yolu (.txt):", style=self.ui.custom_style).ask()
        if not file_path:
            return
            
        success, msg = self.tt_downloader.validate_tiktok_cookies(file_path)
        if success:
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
        import questionary
        file_path = questionary.text("Facebook Cookie dosyası yolu (.txt):", style=self.ui.custom_style).ask()
        if not file_path:
            return
            
        success, msg = self.fb_downloader.validate_facebook_cookies(file_path)
        if success:
            self.config.save()
            self.ui.show_success("Facebook bağlantısı başarılı!")
            self.logger.auth_event("facebook", True, "cookies")
        else:
            self.ui.show_error(f"Hata: {msg}")
            self.logger.auth_event("facebook", False, "cookies")
            
        self.ui.wait_for_enter()
