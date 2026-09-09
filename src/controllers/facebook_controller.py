"""
Facebook Controller
Handles all Facebook-related UI operations.
"""

from pathlib import Path
from typing import Any

from src.controllers.base import BaseController
from src.core.facebook import FacebookDownloader


class FacebookController(BaseController):
    """Controller for Facebook operations."""
    
    def __init__(self, config: Any, ui: Any):
        super().__init__(config, ui)
        self.downloader = FacebookDownloader(config)
    
    def run(self) -> None:
        """Main Facebook menu loop."""
        self.ui.push_breadcrumb("Facebook")
        
        try:
            while True:
                self.ui.print_header(self.config.download_path)
                
                import questionary
                choices = [
                    "Tek Video İndir",
                    "Toplu İndir (URL Listesi)",
                    "URL Çıkarma Scriptleri",
                    "Geri Dön"
                ]
                
                choice = questionary.select(
                    "Facebook İşlemleri:",
                    choices=choices,
                    style=self.ui.custom_style
                ).ask()
                
                if not choice or "Geri Dön" in choice:
                    break
                
                try:
                    if "Tek Video" in choice:
                        self.handle_single()
                    elif "Toplu İndir" in choice:
                        self.handle_bulk()
                    elif "URL Çıkarma" in choice:
                        self.show_extractor_script()
                except Exception as e:
                    self.handle_error(e, "Facebook operation")
        finally:
            if self.downloader.driver:
                self.downloader.close_selenium()
            self.ui.pop_breadcrumb()

    def handle_single(self) -> None:
        """Download a single Facebook video."""
        import questionary
        url = questionary.text("Facebook Video URL:", style=self.ui.custom_style).ask()
        if not url:
            return
            
        self.ui.console.print(f"\n[bold green]İndiriliyor...[/bold green] [dim]{url}[/dim]\n")
        self.logger.download_start("facebook", url)
        
        success, message = self.downloader.download(url)
        
        if success:
            self.ui.show_success(message)
            self.logger.download_success("facebook", url)
        else:
            self.ui.show_error(message)
            self.logger.download_fail("facebook", url, message)
            
        self.ui.wait_for_enter()

    def handle_bulk(self) -> None:
        """Download multiple Facebook videos from a file."""
        import questionary
        file_path = questionary.text("URL Listesi Dosya Yolu:", style=self.ui.custom_style).ask()
        if not file_path:
            return
            
        self.ui.console.print("\n[bold cyan]Toplu İndirme Başlatılıyor...[/bold cyan]\n")
        
        successful, failed, skipped, failed_urls = self.downloader.download_bulk(
            file_path,
            progress_callback=self.ui.show_progress
        )
        
        self.ui.show_summary(successful, failed, failed_urls, skipped)
        self.ui.wait_for_enter()

    def show_extractor_script(self) -> None:
        """Show Facebook URL extraction options."""
        self.ui.clear_screen()
        
        # Method 1: Universal UserScript
        script_path = self.get_resource_path("scripts/universal_video_collector.user.js")
        
        self.ui.console.print("\n[bold cyan]Seçenek 1: Tampermonkey Script (Tavsiye Edilen)[/bold cyan]")
        self.ui.console.print(
            f"[dim]Dosya Konumu:[/dim] [white]{script_path}[/white]\n"
            "[dim]Bu dosyayı Tampermonkey eklentisine ekleyerek Facebook, TikTok ve Twitter "
            "üzerinde gelişmiş bir toplama paneli kullanabilirsiniz.[/dim]\n"
        )
        
        # Method 2: Console Script
        self.ui.console.print("[bold cyan]Seçenek 2: Tarayıcı Konsol Scripti[/bold cyan]")
        script = self.downloader.get_url_extraction_script()
        self.ui.show_url_extraction_script(script)
        
        self.ui.wait_for_enter()
