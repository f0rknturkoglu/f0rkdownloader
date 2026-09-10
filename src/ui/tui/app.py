"""
Textual Modern Dashboard TUI
Provides a rich terminal user interface with sidebar navigation, live progress,
and direct multi-platform downloading.
"""

import threading
from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    ProgressBar,
    RichLog,
    Select,
    Static,
)

from src.config import Config
from src.core.facebook import FacebookDownloader
from src.core.instagram import InstagramDownloader
from src.core.pinterest import PinterestDownloader
from src.core.tiktok import TikTokDownloader
from src.core.twitter import TwitterDownloader
from src.core.youtube import YoutubeDownloader
from src.utils.bridge import GLOBAL_BRIDGE_QUEUE, LocalBridgeServer
from src.utils.clipboard_watcher import ClipboardWatcher


class SidebarItem(ListItem):
    def __init__(self, key: str, label: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key = key
        self.label_text = label

    def compose(self) -> ComposeResult:
        yield Label(self.label_text)


class F0rkDownloaderTUI(App):
    """Modern Textual Dashboard for f0rkdownloader."""

    CSS = """
    Screen {
        background: #0f172a;
        color: #f8fafc;
    }

    #app-grid {
        height: 100%;
        layout: horizontal;
    }

    #sidebar {
        width: 30;
        background: #1e293b;
        border-right: heavy #334155;
        padding: 1;
    }

    #sidebar-title {
        text-style: bold;
        color: #38bdf8;
        margin-bottom: 1;
        text-align: center;
    }

    #main-content {
        width: 1fr;
        padding: 1 2;
    }

    .section-title {
        text-style: bold;
        color: #f1f5f9;
        margin-top: 1;
        margin-bottom: 1;
    }

    #url-input {
        margin-bottom: 1;
        border: tall #0284c7;
    }

    #action-bar {
        height: 3;
        margin-bottom: 1;
    }

    #action-bar Button {
        margin-right: 1;
    }

    #progress-container {
        height: 4;
        background: #1e293b;
        border: solid #334155;
        padding: 1;
        margin-bottom: 1;
    }

    #log-console {
        height: 1fr;
        background: #090d16;
        border: solid #1e293b;
        padding: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Çıkış"),
        ("d", "start_download", "İndir"),
        ("c", "clear_console", "Konsolu Temizle"),
    ]

    def __init__(self, config: Config | None = None, **kwargs):
        super().__init__(**kwargs)
        self.config = config or Config()
        self.current_platform = "youtube"

        # Downloaders
        self.downloaders = {
            "youtube": YoutubeDownloader(self.config),
            "tiktok": TikTokDownloader(self.config),
            "twitter": TwitterDownloader(self.config),
            "facebook": FacebookDownloader(self.config),
            "instagram": InstagramDownloader(self.config),
            "pinterest": PinterestDownloader(self.config),
        }

        # Services
        self.bridge_server = LocalBridgeServer()
        self.bridge_server.start()

        self.clipboard_watcher = ClipboardWatcher(on_link_found=self._on_clipboard_detected)
        self.clipboard_watcher.start()

    def _on_clipboard_detected(self, url: str, platform: str) -> None:
        self.call_from_thread(self._handle_incoming_url, url, platform)

    def _handle_incoming_url(self, url: str, platform: str) -> None:
        log = self.query_one("#log-console", RichLog)
        log.write(f"[bold cyan][Pano Algılandı - {platform.upper()}][/bold cyan] {url}")
        inp = self.query_one("#url-input", Input)
        if not inp.value:
            inp.value = url
            self.current_platform = platform
            title_lbl = self.query_one("#platform-title", Label)
            title_lbl.update(f"Seçili Platform: [bold green]{platform.upper()}[/bold green]")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="app-grid"):
            with Vertical(id="sidebar"):
                yield Label("f0rkdownloader", id="sidebar-title")
                yield Label("[dim]-- Platformlar --[/dim]")
                with ListView(id="platform-list"):
                    yield SidebarItem("youtube", "  YouTube")
                    yield SidebarItem("tiktok", "  TikTok")
                    yield SidebarItem("twitter", "  Twitter/X")
                    yield SidebarItem("facebook", "  Facebook")
                    yield SidebarItem("instagram", "  Instagram")
                    yield SidebarItem("pinterest", "  Pinterest")
                yield Label("[dim]-- Servisler --[/dim]", classes="section-title")
                yield Label("Pano İzleyici: [green]Aktif[/green]")
                yield Label("HTTP Köprüsü: [green]:48123[/green]")

            with Vertical(id="main-content"):
                yield Label(f"Seçili Platform: [bold green]{self.current_platform.upper()}[/bold green]", id="platform-title")
                yield Input(placeholder="İndirilecek video URL'sini yapıştırın...", id="url-input")

                with Horizontal(id="action-bar"):
                    yield Button("İndir", id="btn-download", variant="success")
                    yield Button("Klasör Tara (Toplu)", id="btn-auto-scan", variant="primary")
                    yield Button("Köprü Kuyruğunu İndir", id="btn-bridge-queue", variant="warning")
                    yield Button("Konsolu Temizle", id="btn-clear", variant="default")

                with Vertical(id="progress-container"):
                    yield Label("İlerleme:", id="progress-label")
                    yield ProgressBar(id="download-progress", show_percentage=True, show_eta=True)

                yield Label("Canlı İndirme ve İşlem Günlüğü:", classes="section-title")
                yield RichLog(id="log-console", highlight=True, markup=True)

        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, SidebarItem):
            self.current_platform = event.item.key
            title_lbl = self.query_one("#platform-title", Label)
            title_lbl.update(f"Seçili Platform: [bold green]{self.current_platform.upper()}[/bold green]")
            log = self.query_one("#log-console", RichLog)
            log.write(f"[yellow]Platform değiştirildi:[/yellow] {self.current_platform.upper()}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-download":
            self.action_start_download()
        elif event.button.id == "btn-auto-scan":
            self._start_auto_scan()
        elif event.button.id == "btn-bridge-queue":
            self._process_bridge_queue()
        elif event.button.id == "btn-clear":
            self.action_clear_console()

    def action_clear_console(self) -> None:
        log = self.query_one("#log-console", RichLog)
        log.clear()

    def action_start_download(self) -> None:
        url_input = self.query_one("#url-input", Input)
        url = url_input.value.strip()
        if not url:
            log = self.query_one("#log-console", RichLog)
            log.write("[bold red]Lütfen geçerli bir URL girin![/bold red]")
            return

        self.run_worker(lambda: self._download_worker(url, self.current_platform), thread=True)

    def _download_worker(self, url: str, platform: str) -> None:
        downloader = self.downloaders.get(platform)
        if not downloader:
            return

        log = self.query_one("#log-console", RichLog)
        log.write(f"[bold cyan]İndirme Başlatılıyor ({platform.upper()}):[/bold cyan] {url}")

        def progress_hook(d):
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 1
                downloaded = d.get("downloaded_bytes") or 0
                pct = (downloaded / total) * 100
                pb = self.query_one("#download-progress", ProgressBar)
                self.call_from_thread(pb.update, progress=pct)

        success, msg = downloader.download(url, progress_hooks=[progress_hook])
        if success:
            log.write(f"[bold green]Başarılı:[/bold green] {msg}")
        else:
            log.write(f"[bold red]Hata:[/bold red] {msg}")

    def _start_auto_scan(self) -> None:
        downloader = self.downloaders.get(self.current_platform)
        if not downloader:
            return

        log = self.query_one("#log-console", RichLog)
        log.write("[dim]İndirilenler klasörü taranıyor...[/dim]")

        import os
        from pathlib import Path
        downloads = Path(os.path.expanduser("~")) / "Downloads"
        candidates = sorted(downloads.glob("*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
        valid = [c for c in candidates if "cookie" not in c.name.lower()]

        if not valid:
            log.write("[red]İndirilenler klasöründe txt bulunamadı![/red]")
            return

        target_file = str(valid[0])
        log.write(f"[green]Liste bulundu:[/green] {target_file}")

        def bulk_worker():
            def prog(curr, tot, u, ok, m):
                self.call_from_thread(
                    log.write,
                    f"[{curr}/{tot}] {u[:45]}... -> {'[green]OK[/green]' if ok else '[red]Hata[/red]'}"
                )
            downloader.bulk_download_from_file(target_file, progress_callback=prog)

        self.run_worker(bulk_worker, thread=True)

    def _process_bridge_queue(self) -> None:
        batches = GLOBAL_BRIDGE_QUEUE.get_all_pending()
        log = self.query_one("#log-console", RichLog)
        if not batches:
            log.write("[yellow]Köprü kuyruğunda bekleyen link yok.[/yellow]")
            return

        def queue_worker():
            for b in batches:
                plat = b["platform"]
                urls = b["urls"]
                log.write(f"[cyan]{plat.upper()} kuyruğundan {len(urls)} link indiriliyor...[/cyan]")
                downloader = self.downloaders.get(plat) or self.downloaders["youtube"]
                downloader.bulk_download(urls)

        self.run_worker(queue_worker, thread=True)

    def on_unmount(self) -> None:
        self.bridge_server.stop()
        self.clipboard_watcher.stop()
