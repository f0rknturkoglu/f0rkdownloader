"""
Twitter Controller
Handles all Twitter/X-related operations.
"""

from pathlib import Path

from src.controllers.base import BaseController
from src.core.twitter import TwitterDownloader


class TwitterController(BaseController):
    """Controller for Twitter/X operations."""
    
    def __init__(self, config, ui):
        super().__init__(config, ui)
        self.downloader = TwitterDownloader(config)
    
    def run(self) -> None:
        """Main Twitter menu loop."""
        self.ui.push_breadcrumb("Twitter/X")
        
        while True:
            self.ui.print_header(self.config.download_path)
            self._show_status()
            
            import questionary
            choices = [
                "Tek Link ile İndir",
                "Toplu İndir (Dosyadan)",
                "Bookmarks İndir (Profil)",
                "URL Çıkarma Scriptleri",
                "Geri Dön"
            ]
            
            choice = questionary.select(
                "Twitter İşlemleri:",
                choices=choices,
                style=self.ui.custom_style
            ).ask()
            
            if not choice or "Geri Dön" in choice:
                break
            
            try:
                if "Bookmarks" in choice:
                    self.handle_bookmarks()
                elif "Tek Link" in choice:
                    self.handle_single()
                elif "Toplu İndir" in choice:
                    self.handle_bulk()
                elif "URL Çıkarma" in choice:
                    self.handle_show_script()
            except Exception as e:
                self.handle_error(e, "Twitter operation")
        
        self.ui.pop_breadcrumb()
    
    def _show_status(self) -> None:
        """Show Twitter connection status."""
        if self.config.twitter_cookies_file:
            tw_name = self.config.twitter_username or "Bağlı"
            self.ui.console.print(
                f"[green]● Twitter[/green]: @{tw_name}",
                justify="center",
            )
        else:
            self.ui.console.print(
                "[dim]● Twitter Bağlı Değil (Bookmarks için Hesap İşlemlerinden bağlanın)[/dim]",
                justify="center",
            )
    
    def handle_bookmarks(self) -> None:
        """Download Twitter bookmarks."""
        if not self.config.twitter_cookies_file:
            self.ui.show_error("Bookmarks için önce Twitter hesabınızı bağlamanız gerekir.")
            self.ui.wait_for_enter()
            return

        self.ui.console.print("\n[bold cyan]Bookmarks taranıyor...[/bold cyan]\n")
        self.logger.info("Fetching Twitter bookmarks")
        
        bookmarks = self.downloader.get_bookmarks()
        
        if not bookmarks:
            self.ui.show_error(
                "Bookmark bulunamadı veya erişilemedi.\n"
                "Cookie dosyanızın geçerli olduğundan emin olun."
            )
            self.ui.wait_for_enter()
            return
        
        self.ui.console.print(f"[green]✓ {len(bookmarks)} bookmark bulundu![/green]\n")
        
        if not self.ui.ask_confirmation(f"{len(bookmarks)} bookmark indirilsin mi?"):
            return
        
        self.ui.console.print("\n[bold cyan]İndirme başlıyor...[/bold cyan]\n")
        self.logger.info(f"Starting bookmark download: {len(bookmarks)} items")
        
        successful, failed, skipped, failed_urls = self.downloader.download_bookmarks(
            progress_callback=self.ui.show_progress,
        )
        
        self.ui.show_summary(successful, failed, failed_urls, skipped)
        self.logger.info(f"Bookmarks complete: success={successful}, failed={failed}, skipped={skipped}")
        self.ui.wait_for_enter()
    
    def handle_single(self) -> None:
        """Download single Twitter video."""
        import questionary
        url = questionary.text("Tweet URL:", style=self.ui.custom_style).ask()
        if not url:
            return
        
        self.ui.console.print(f"\n[bold green]İndiriliyor...[/bold green] [dim]{url}[/dim]\n")
        self.logger.download_start("twitter", url)
        
        try:
            success, message = self.downloader.download(url)
            
            if success:
                self.ui.show_success(f"Twitter videosu indirildi!\nKonum: {self.downloader.twitter_download_path}")
                self.logger.download_success("twitter", url)
            elif "zaten indirilmiş" in message:
                self.ui.console.print(f"[yellow]○ {message}[/yellow]")
            else:
                self.ui.show_error(f"İndirme hatası: {message}")
                self.logger.download_fail("twitter", url, message)
        except Exception as e:
            self.handle_error(e, "Twitter single download")
        
        self.ui.wait_for_enter()
    
    def handle_bulk(self) -> None:
        """Download multiple Twitter videos from file."""
        import questionary
        file_path = questionary.text("URL Listesi Dosya Yolu (.txt):", style=self.ui.custom_style).ask()
        if not file_path:
            return
        
        self.ui.print_header(self.config.download_path)
        
        try:
            urls = self.downloader.read_urls_from_file(file_path)
            self.ui.console.print(
                f"\n[bold cyan]Toplu İndirme Başlıyor[/bold cyan]\n"
                f"[dim]Dosya: {file_path}[/dim]\n"
                f"[dim]Toplam URL: {len(urls)}[/dim]\n"
            )
            self.logger.info(f"Twitter bulk download: {len(urls)} URLs from {file_path}")
            
            successful, failed, skipped, failed_urls = self.downloader.bulk_download(
                urls,
                progress_callback=self.ui.show_progress,
            )
            
            self.ui.show_summary(successful, failed, failed_urls, skipped)
            self.logger.info(f"Bulk complete: success={successful}, failed={failed}, skipped={skipped}")
        
        except FileNotFoundError as e:
            self.ui.show_error(str(e))
        except ValueError as e:
            self.ui.show_error(str(e))
        
        self.ui.wait_for_enter()

    def handle_show_script(self) -> None:
        """Show Twitter URL extraction options."""
        self.ui.clear_screen()
        
        # Option 1: Universal Script
        script_path = self.get_resource_path("scripts/universal_video_collector.user.js")
        self.ui.console.print("\n[bold cyan]Seçenek 1: Universal Tampermonkey Script[/bold cyan]")
        self.ui.console.print(
            f"[dim]Dosya Konumu:[/dim] [white]{script_path}[/white]\n"
            "[dim]Bu scripti kullanarak tarayıcı üzerinde gelişmiş bir panel ile video toplayabilirsiniz.[/dim]\n"
        )
        
        # Option 2: Console Script
        self.ui.console.print("[bold cyan]Seçenek 2: Basit Konsol Scripti[/bold cyan]")
        script = self.downloader.get_url_extraction_script()
        self.ui.show_url_extraction_script(script)
        
        self.ui.wait_for_enter()
