"""
Pinterest Controller
Handles all Pinterest-related UI operations.
"""

import os
from pathlib import Path
from typing import Any

from src.controllers.base import BaseController
from src.core.pinterest import PinterestDownloader


class PinterestController(BaseController):
    """Controller for Pinterest operations."""

    def __init__(self, config: Any, ui: Any):
        super().__init__(config, ui)
        self.downloader = PinterestDownloader(config)

    def run(self) -> None:
        """Main Pinterest menu loop."""
        self.ui.push_breadcrumb("Pinterest")

        while True:
            self.ui.print_header(self.config.download_path)

            import questionary
            choices = [
                "Tek Pin İndir (Video / Görsel)",
                "⚡ İndirilenler Klasörünü Tara ve Toplu İndir (TEK TIK)",
                "Toplu İndir (URL Listesi Seçmeli)",
                "Geri Dön"
            ]

            choice = questionary.select(
                "Pinterest İşlemleri:",
                choices=choices,
                style=self.ui.custom_style
            ).ask()

            if not choice or "Geri Dön" in choice:
                break

            try:
                if "Tek Pin" in choice:
                    self.handle_single()
                elif "Tara ve Toplu İndir" in choice:
                    self.handle_auto_scan()
                elif "Toplu İndir" in choice:
                    self.handle_bulk_file()
            except Exception as e:
                self.handle_error(e, "Pinterest operation")

        self.ui.pop_breadcrumb()

    def handle_single(self) -> None:
        """Download a single Pinterest Pin."""
        import questionary
        url = questionary.text("Pinterest Pin URL:", style=self.ui.custom_style).ask()
        if not url:
            return

        self.ui.console.print(f"\n[bold green]İndiriliyor...[/bold green] [dim]{url}[/dim]\n")
        self.logger.download_start("pinterest", url)

        success, message = self.downloader.download(url)

        if success:
            self.ui.show_success(message)
            self.logger.download_success("pinterest", url)
        else:
            self.ui.show_error(message)
            self.logger.download_fail("pinterest", url, message)

        self.ui.wait_for_enter()

    def _execute_bulk(self, file_path: str) -> None:
        """Execute bulk download from a file path."""
        self.ui.console.print("\n[bold cyan]Toplu İndirme Başlatılıyor...[/bold cyan]\n")
        successful, failed, skipped, failed_urls = self.downloader.bulk_download_from_file(
            file_path,
            progress_callback=self.ui.show_progress
        )
        self.ui.show_summary(successful, failed, failed_urls, skipped)
        self.ui.wait_for_enter()

    def handle_auto_scan(self) -> None:
        """Automatically detect the latest Pinterest URL list in Downloads folder."""
        downloads_folder = Path(os.path.expanduser("~")) / "Downloads"
        if not downloads_folder.exists():
            self.ui.show_error("Downloads klasörü bulunamadı.")
            self.ui.wait_for_enter()
            return

        txt_files = sorted(
            downloads_folder.glob("*.txt"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        candidates = [
            f for f in txt_files
            if "cookie" not in f.name.lower()
            and ("pinterest" in f.name.lower() or "f0rkn" in f.name.lower() or "url" in f.name.lower())
        ]

        if not candidates:
            candidates = [f for f in txt_files if "cookie" not in f.name.lower()]

        if not candidates:
            self.ui.show_warning("İndirilenler klasöründe geçerli bir .txt listesi bulunamadı.")
            self.ui.wait_for_enter()
            return

        target_file = candidates[0]
        self.ui.console.print(f"[green]Otomatik bulunan liste:[/green] [bold]{target_file.name}[/bold]")
        self._execute_bulk(str(target_file))

    def handle_bulk_file(self) -> None:
        """Let user select or enter a URL list file."""
        import questionary
        downloads_folder = Path(os.path.expanduser("~")) / "Downloads"
        txt_files = []
        if downloads_folder.exists():
            txt_files = sorted(
                downloads_folder.glob("*.txt"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )[:10]

        choices = [f"[Dosya] {f.name}" for f in txt_files if "cookie" not in f.name.lower()]
        choices.append("Manuel Dosya Yolu Gir...")
        choices.append("İptal")

        sel = questionary.select("URL Listesi Seçin:", choices=choices, style=self.ui.custom_style).ask()
        if not sel or sel == "İptal":
            return

        if sel == "Manuel Dosya Yolu Gir...":
            path_str = questionary.text("Dosya Yolu:", style=self.ui.custom_style).ask()
            if not path_str:
                return
            self._execute_bulk(path_str.strip('"').strip("'"))
        else:
            filename = sel.replace("[Dosya] ", "")
            target_path = downloads_folder / filename
            self._execute_bulk(str(target_path))
