"""
TikTok Controller
Handles all TikTok-related UI operations.
"""

import os
from pathlib import Path
from typing import Any

from src.controllers.base import BaseController
from src.core.tiktok import TikTokDownloader


class TikTokController(BaseController):
    """Controller for TikTok operations."""
    
    def __init__(self, config: Any, ui: Any):
        super().__init__(config, ui)
        self.downloader = TikTokDownloader(config)
    
    def run(self) -> None:
        """Main TikTok menu loop."""
        self.ui.push_breadcrumb("TikTok")
        
        while True:
            self.ui.print_header(self.config.download_path)
            
            import questionary
            choices = [
                "Tek Video İndir",
                "Toplu İndir (URL Listesi)",
                "Beğenilen Videoları İndir",
                "Favori Videoları İndir",
                "TikTok Veri Export'u Kullan",
                "URL Çıkarma Scriptleri",
                "Geri Dön"
            ]
            
            choice = questionary.select(
                "TikTok İşlemleri:",
                choices=choices,
                style=self.ui.custom_style
            ).ask()
            
            if not choice or "Geri Dön" in choice:
                break
            
            try:
                if "Tek Video" in choice:
                    self.handle_single()
                elif "Toplu İndir" in choice:
                    self.handle_bulk_file()
                elif "Beğenilen" in choice:
                    self.handle_liked()
                elif "Favori" in choice:
                    self.handle_favorites()
                elif "Veri Export" in choice:
                    self.handle_data_export()
                elif "URL Çıkarma" in choice:
                    self.handle_show_script()
            except Exception as e:
                self.handle_error(e, "TikTok operation")
                
        self.ui.pop_breadcrumb()

    def handle_single(self) -> None:
        """Download a single TikTok video."""
        import questionary
        url = questionary.text("TikTok URL:", style=self.ui.custom_style).ask()
        if not url:
            return
            
        self.ui.console.print(f"\n[bold green]İndiriliyor...[/bold green] [dim]{url}[/dim]\n")
        self.logger.download_start("tiktok", url)
        
        success, message = self.downloader.download(url)
        
        if success:
            self.ui.show_success(message)
            self.logger.download_success("tiktok", url)
        else:
            self.ui.show_error(message)
            self.logger.download_fail("tiktok", url, message)
            
        self.ui.wait_for_enter()

    def handle_bulk_file(self) -> None:
        """Download videos from a text file."""
        import questionary
        file_path = questionary.text("URL Listesi Dosya Yolu:", style=self.ui.custom_style).ask()
        if not file_path:
            return
            
        self.ui.console.print("\n[bold cyan]Toplu İndirme Başlatılıyor...[/bold cyan]\n")
        
        successful, failed, skipped, failed_urls = self.downloader.bulk_download_from_file(
            file_path, 
            progress_callback=self.ui.show_progress
        )
        
        self.ui.show_summary(successful, failed, failed_urls, skipped)
        self.ui.wait_for_enter()

    def handle_liked(self) -> None:
        """Download liked videos from exported file."""
        import questionary
        file_path = questionary.text("Beğenilenler URL Listesi Dosya Yolu:", style=self.ui.custom_style).ask()
        if not file_path:
            return
            
        self.ui.console.print("\n[bold cyan]Beğenilen Videolar İndiriliyor...[/bold cyan]\n")
        
        successful, failed, skipped, failed_urls = self.downloader.download_liked_videos(
            file_path,
            progress_callback=self.ui.show_progress
        )
        
        self.ui.show_summary(successful, failed, failed_urls, skipped)
        self.ui.wait_for_enter()

    def handle_favorites(self) -> None:
        """Download favorite videos from exported file."""
        import questionary
        file_path = questionary.text("Favoriler URL Listesi Dosya Yolu:", style=self.ui.custom_style).ask()
        if not file_path:
            return
            
        self.ui.console.print("\n[bold cyan]Favori Videolar İndiriliyor...[/bold cyan]\n")
        
        successful, failed, skipped, failed_urls = self.downloader.download_bookmarked_videos(
            file_path,
            progress_callback=self.ui.show_progress
        )
        
        self.ui.show_summary(successful, failed, failed_urls, skipped)
        self.ui.wait_for_enter()

    def handle_show_script(self) -> None:
        """Show TikTok URL extraction script options."""
        self.ui.clear_screen()
        
        # Option 1: Universal Script
        script_path = self.get_resource_path("scripts/universal_video_collector.user.js")
        self.ui.console.print("\n[bold magenta]Seçenek 1: Universal Tampermonkey Script[/bold magenta]")
        self.ui.console.print(
            f"[dim]Dosya Konumu:[/dim] [white]{script_path}[/white]\n"
            "[dim]Bu scripti kullanarak tarayıcı üzerinde gelişmiş bir panel ile video toplayabilirsiniz.[/dim]\n"
        )
        
        # Option 2: Console Script
        self.ui.console.print("[bold magenta]Seçenek 2: Basit Konsol Scripti[/bold magenta]")
        script = self.downloader.get_url_extraction_script()
        self.ui.show_url_extraction_script(script)
        
        self.ui.wait_for_enter()

    def handle_data_export(self) -> None:
        """Download TikTok videos from data export file."""
        import questionary
        file_path = questionary.text("TikTok Veri Export Dosyası (ZIP veya JSON):", style=self.ui.custom_style).ask()
        if not file_path or not os.path.exists(file_path):
            return
            
        category = questionary.select(
            "Hangi kategoriyi indirmek istersiniz?",
            choices=["liked", "favorites", "watched"],
            style=self.ui.custom_style
        ).ask()
        
        if not category:
            return
            
        urls = self.downloader.get_data_export_urls(file_path, category)
        self.ui.console.print(f"\n[green]✓ {len(urls)} adet video bulundu![/green]\n")
        
        if not self.ui.ask_confirmation("İndirmeye başlansın mı?"):
            return
            
        successful, failed, skipped, failed_urls = self.downloader.bulk_download(
            urls,
            progress_callback=self.ui.show_progress
        )
        
        self.ui.show_summary(successful, failed, failed_urls, skipped)
        self.ui.wait_for_enter()
