"""
YouTube Controller
Handles all YouTube-related UI operations.
"""

import os
from typing import Any
from src.controllers.base import BaseController
from src.core.youtube import YoutubeDownloader


class YouTubeController(BaseController):
    """Controller for YouTube operations."""
    
    def __init__(self, config: Any, ui: Any):
        super().__init__(config, ui)
        self.downloader = YoutubeDownloader(config)
    
    def run(self) -> None:
        """Main YouTube menu loop."""
        self.ui.push_breadcrumb("YouTube")
        
        while True:
            self.ui.print_header(self.config.download_path)
            choice = self.ui.ask_youtube_menu()
            
            if not choice or "Geri Dön" in choice:
                break
            
            try:
                if "Link ile İndir" in choice:
                    self.handle_single_download()
                elif "YouTube'da Ara" in choice:
                    self.handle_search()
                elif "Kütüphanemden İndir" in choice:
                    self.handle_library_download()
                elif "İndirilenleri Yönet" in choice:
                    self.handle_manage_downloads()
            except Exception as e:
                self.handle_error(e, "YouTube operation")
                
        self.ui.pop_breadcrumb()

    def handle_single_download(self) -> None:
        """Handle link-based download."""
        url = self.ui.console.input("\n[bold cyan]YouTube URL (Video veya Playlist):[/bold cyan] ").strip()
        if not url:
            return
            
        self.ui.console.print(f"\n[bold green]İndiriliyor...[/bold green] [dim]{url}[/dim]\n")
        self.logger.download_start("youtube", url)
        
        success, message = self.downloader.download(url)
        
        if success:
            self.ui.show_success(message)
            self.logger.download_success("youtube", url)
        else:
            self.ui.show_error(message)
            self.logger.download_fail("youtube", url, message)
            
        self.ui.wait_for_enter()

    def handle_search(self) -> None:
        """Handle YouTube search and download."""
        query = self.ui.console.input("\n[bold cyan]Arama Terimi:[/bold cyan] ").strip()
        if not query:
            return
            
        self.ui.console.print(f"\n[dim]'{query}' aranıyor...[/dim]")
        results = self.downloader.search(query)
        
        if not results:
            self.ui.show_error("Sonuç bulunamadı.")
            self.ui.wait_for_enter()
            return
            
        # Display results and ask to select
        choices = [
            f"{r['title']} | [dim]{r['channel']} ({r['duration']}s)[/dim]" 
            for r in results
        ]
        choices.append("Geri Dön")
        
        import questionary
        selected = questionary.select(
            "Hangi videoyu indirmek istersiniz?",
            choices=choices,
            style=self.ui.custom_style
        ).ask()
        
        if not selected or selected == "Geri Dön":
            return
            
        # Find index
        idx = choices.index(selected)
        video = results[idx]
        
        self.ui.console.print(f"\n[bold green]İndiriliyor:[/bold green] {video['title']}\n")
        success, message = self.downloader.download(video['url'])
        
        if success:
            self.ui.show_success(message)
        else:
            self.ui.show_error(message)
            
        self.ui.wait_for_enter()

    def handle_library_download(self) -> None:
        """Handle library/special playlist downloads."""
        self.ui.show_info("Bu özellik yakında eklenecek.")
        self.ui.wait_for_enter()

    def handle_manage_downloads(self) -> None:
        """Open download folder."""
        path = self.downloader.youtube_path
        self.ui.show_info(f"İndirilenler burada: {path}")
        if os.name == 'nt':
            os.startfile(path)
        else:
            import subprocess
            subprocess.run(['open', str(path)])
        self.ui.wait_for_enter()
