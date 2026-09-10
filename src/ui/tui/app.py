"""
Modern Textual TUI Application for f0rkdownloader
Provides a full-featured, modular dashboard giving 100% access to all platforms,
automation services, settings, account cookies, search, and download history.
"""

import json
import os
from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    ContentSwitcher,
    DataTable,
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
from src.controllers.base import BaseController
from src.core.facebook import FacebookDownloader
from src.core.instagram import InstagramDownloader
from src.core.pinterest import PinterestDownloader
from src.core.tiktok import TikTokDownloader
from src.core.twitter import TwitterDownloader
from src.core.youtube import YoutubeDownloader
from src.ui.tui.modals import FilePromptModal, FormatPickerModal, SearchModal
from src.ui.tui.panes import (
    AccountsPane,
    BridgePane,
    ClipboardPane,
    HistoryPane,
    PlatformPane,
    SettingsPane,
    WatcherPane,
    open_folder_in_file_manager,
)
from src.utils.bridge import GLOBAL_BRIDGE_QUEUE, LocalBridgeServer
from src.utils.channel_watcher import ChannelWatcher
from src.utils.clipboard_watcher import ClipboardWatcher


class SidebarItem(ListItem):
    def __init__(self, key: str, label: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key = key
        self.label_text = label

    def compose(self) -> ComposeResult:
        yield Label(self.label_text)


class F0rkDownloaderTUI(App):
    """Full-featured Textual Dashboard for f0rkdownloader."""

    CSS = """
    Screen {
        background: #090d16;
        color: #f8fafc;
    }

    #app-grid {
        height: 100%;
        layout: horizontal;
    }

    #sidebar {
        width: 32;
        background: #0f172a;
        border-right: heavy #1e293b;
        padding: 1;
    }

    #sidebar-title {
        text-style: bold;
        color: #38bdf8;
        margin-bottom: 1;
        text-align: center;
    }

    .sidebar-category {
        color: #64748b;
        text-style: bold;
        margin-top: 1;
        margin-bottom: 0;
        padding-left: 1;
    }

    #sidebar-list {
        background: transparent;
        height: auto;
    }

    #sidebar-list ListItem {
        padding: 0 1;
        height: 2;
    }

    #sidebar-list ListItem:hover {
        background: #1e293b;
    }

    #sidebar-list ListItem.-selected {
        background: #0284c7;
        color: #ffffff;
    }

    #main-area {
        width: 1fr;
        padding: 1;
    }

    #main-switcher {
        height: 1fr;
    }

    .pane-title {
        text-style: bold;
        font-size: 16;
        color: #38bdf8;
        margin-bottom: 1;
    }

    .setting-label {
        text-style: bold;
        color: #cbd5e1;
        margin-top: 1;
        margin-bottom: 0;
    }

    .setting-info {
        color: #94a3b8;
        margin-bottom: 1;
    }

    .url-bar {
        height: 3;
        margin-bottom: 1;
    }

    .main-url-input {
        width: 1fr;
        border: tall #0284c7;
    }

    .action-row {
        height: 3;
        margin-bottom: 1;
    }

    .action-row Button {
        margin-right: 1;
    }

    .action-row-extra {
        height: 3;
        margin-bottom: 1;
    }

    .action-row-extra Button {
        margin-right: 1;
    }

    #bottom-dock {
        height: 16;
        background: #0f172a;
        border-top: heavy #1e293b;
        padding: 1;
    }

    #progress-bar-container {
        height: 3;
        margin-bottom: 1;
    }

    #log-console {
        height: 11;
        background: #020617;
        border: solid #1e293b;
        padding: 0 1;
    }

    DataTable {
        height: 10;
        border: solid #1e293b;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Çıkış"),
        ("d", "quick_download", "Hızlı İndir"),
        ("c", "clear_console", "Konsolu Temizle"),
        ("o", "open_folder", "Klasörü Aç"),
    ]

    def __init__(self, config: Config | None = None, **kwargs):
        super().__init__(**kwargs)
        self.config = config or Config()
        self.current_platform = "youtube"

        # Download Engines
        self.downloaders = {
            "youtube": YoutubeDownloader(self.config),
            "tiktok": TikTokDownloader(self.config),
            "twitter": TwitterDownloader(self.config),
            "facebook": FacebookDownloader(self.config),
            "instagram": InstagramDownloader(self.config),
            "pinterest": PinterestDownloader(self.config),
        }

        # Automation Services
        self.bridge_server = LocalBridgeServer()
        self.bridge_server.start()

        self.channel_watcher = ChannelWatcher(Path(self.config.base_download_path))
        self.clipboard_watcher = ClipboardWatcher(on_link_found=self._on_clipboard_detected)
        self.clipboard_watcher.start()

    def _on_clipboard_detected(self, url: str, platform: str) -> None:
        self.call_from_thread(self._handle_incoming_clipboard_url, url, platform)

    def _handle_incoming_clipboard_url(self, url: str, platform: str) -> None:
        log = self.query_one("#log-console", RichLog)
        log.write(f"[bold green][Pano Algılandı - {platform.upper()}][/bold green] {url}")
        GLOBAL_BRIDGE_QUEUE.add_batch(platform, [url])
        # Update clipboard pane table if visible
        try:
            table = self.query_one("#table-clip-urls", DataTable)
            table.add_row(platform.upper(), url)
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container(id="app-grid"):
            with Vertical(id="sidebar"):
                yield Label("f0rkdownloader", id="sidebar-title")

                yield Label("İNDİRİCİLER", classes="sidebar-category")
                with ListView(id="sidebar-list"):
                    yield SidebarItem("youtube", "  YouTube")
                    yield SidebarItem("tiktok", "  TikTok")
                    yield SidebarItem("twitter", "  Twitter / X")
                    yield SidebarItem("facebook", "  Facebook")
                    yield SidebarItem("instagram", "  Instagram")
                    yield SidebarItem("pinterest", "  Pinterest")

                    yield SidebarItem("clipboard", "  Pano İzleyici")
                    yield SidebarItem("watcher", "  Kanal Takipçisi")
                    yield SidebarItem("bridge", "  Tarayıcı Köprüsü")

                    yield SidebarItem("accounts", "  Hesap & Çerezler")
                    yield SidebarItem("history", "  İndirme Geçmişi")
                    yield SidebarItem("settings", "  Ayarlar")

            with Vertical(id="main-area"):
                with ContentSwitcher(initial="pane-youtube", id="main-switcher"):
                    yield PlatformPane("youtube", "YouTube", id="pane-youtube")
                    yield PlatformPane("tiktok", "TikTok", id="pane-tiktok")
                    yield PlatformPane("twitter", "Twitter / X", id="pane-twitter")
                    yield PlatformPane("facebook", "Facebook", id="pane-facebook")
                    yield PlatformPane("instagram", "Instagram", id="pane-instagram")
                    yield PlatformPane("pinterest", "Pinterest", id="pane-pinterest")

                    yield ClipboardPane(id="pane-clipboard")
                    yield WatcherPane(id="pane-watcher")
                    yield BridgePane(id="pane-bridge")

                    yield AccountsPane(self.config, id="pane-accounts")
                    yield HistoryPane(id="pane-history")
                    yield SettingsPane(self.config, id="pane-settings")

                with Vertical(id="bottom-dock"):
                    with Horizontal(id="progress-bar-container"):
                        yield Label("İlerleme: ", id="lbl-progress-title")
                        yield ProgressBar(id="global-progress", show_percentage=True, show_eta=True)
                    yield RichLog(id="log-console", highlight=True, markup=True)

        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, SidebarItem):
            key = event.item.key
            self.current_platform = key
            switcher = self.query_one("#main-switcher", ContentSwitcher)
            switcher.current = f"pane-{key}"

            log = self.query_one("#log-console", RichLog)
            log.write(f"[dim]Sekme açıldı:[/dim] [bold cyan]{event.item.label_text.strip()}[/bold cyan]")

            if key == "history":
                self._load_history_table()
            elif key == "watcher":
                self._load_watcher_table()
            elif key == "accounts":
                try:
                    self.query_one(AccountsPane).refresh_table()
                except Exception:
                    pass

    # =========================================================================
    # UNIVERSAL ACTION DISPATCHER
    # =========================================================================
    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""

        # Download single
        if btn_id.startswith("btn-dl-") and not (btn_id.startswith("btn-dl-clip") or btn_id.startswith("btn-dl-bridge")):
            plat = btn_id.replace("btn-dl-", "")
            self._start_single_download(plat)

        # Format picker interactive (YouTube)
        elif btn_id == "btn-fmt-youtube":
            self._open_format_picker()

        # Direct MP3 320k
        elif btn_id == "btn-mp3-youtube":
            self._start_mp3_download()

        # Auto Scan (Tek Tık)
        elif btn_id.startswith("btn-scan-") and not btn_id.startswith("btn-scan-all"):
            plat = btn_id.replace("btn-scan-", "")
            self._start_auto_scan(plat)

        # Bulk from file
        elif btn_id.startswith("btn-bulk-"):
            plat = btn_id.replace("btn-bulk-", "")
            self._prompt_bulk_file(plat)

        # Open directory
        elif btn_id.startswith("btn-open-"):
            plat = btn_id.replace("btn-open-", "")
            self._open_platform_folder(plat)

        # YouTube specific
        elif btn_id == "btn-yt-search":
            self._open_search_modal()
        elif btn_id == "btn-yt-library":
            self._start_library_download()

        # TikTok specific
        elif btn_id == "btn-tt-liked":
            self._start_tiktok_liked()
        elif btn_id == "btn-tt-favs":
            self._start_tiktok_favs()
        elif btn_id == "btn-tt-export":
            self._start_tiktok_export()

        # Twitter specific
        elif btn_id == "btn-tw-bookmarks":
            self._start_twitter_bookmarks()

        # Settings
        elif btn_id == "btn-save-settings":
            self._save_settings()
        elif btn_id == "btn-reset-settings":
            self._reset_settings()
        elif btn_id == "btn-open-base-dir":
            open_folder_in_file_manager(self.config.download_path)

        # Accounts
        elif btn_id == "btn-auto-cookies":
            self._auto_bind_cookies()
        elif btn_id == "btn-set-cookie-all":
            self._set_cookie_all()
        elif btn_id == "btn-clear-cookies":
            self._clear_cookies()

        # Automation
        elif btn_id == "btn-toggle-clip":
            self._toggle_clipboard_watcher()
        elif btn_id == "btn-dl-clip-queue" or btn_id == "btn-dl-bridge-queue":
            self._process_bridge_queue()
        elif btn_id == "btn-clear-clip-list":
            self.query_one("#table-clip-urls", DataTable).clear()
        elif btn_id == "btn-add-channel":
            self._add_channel()
        elif btn_id == "btn-remove-channel":
            self._remove_channel()
        elif btn_id == "btn-scan-all-channels":
            self._scan_all_channels()

        # History
        elif btn_id == "btn-refresh-history":
            self._load_history_table()
        elif btn_id == "btn-clear-history":
            self._clear_history()
        elif btn_id == "btn-open-history-dir":
            open_folder_in_file_manager(self.config.download_path)

    # =========================================================================
    # DOWNLOAD WORKERS
    # =========================================================================
    def action_quick_download(self) -> None:
        if self.current_platform in self.downloaders:
            self._start_single_download(self.current_platform)

    def action_clear_console(self) -> None:
        self.query_one("#log-console", RichLog).clear()

    def action_open_folder(self) -> None:
        self._open_platform_folder(self.current_platform)

    def _open_platform_folder(self, plat: str) -> None:
        folder_attr = f"{plat}_path"
        target_dir = getattr(self.config, folder_attr, self.config.download_path)
        open_folder_in_file_manager(target_dir)
        log = self.query_one("#log-console", RichLog)
        log.write(f"[green]Klasör açıldı:[/green] {target_dir}")

    def _start_single_download(self, platform: str, custom_opts: dict | None = None) -> None:
        inp = self.query_one(f"#input-{platform}", Input)
        url = inp.value.strip()
        if not url:
            log = self.query_one("#log-console", RichLog)
            log.write("[bold red]Lütfen geçerli bir URL girin![/bold red]")
            return

        def worker():
            log = self.query_one("#log-console", RichLog)
            log.write(f"\n[bold cyan]İndiriliyor ({platform.upper()}):[/bold cyan] {url}")
            downloader = self.downloaders[platform]

            def progress_hook(d):
                if d.get("status") == "downloading":
                    total = d.get("total_bytes") or d.get("total_bytes_estimate") or 1
                    downloaded = d.get("downloaded_bytes") or 0
                    pct = (downloaded / total) * 100
                    pb = self.query_one("#global-progress", ProgressBar)
                    self.call_from_thread(pb.update, progress=pct)

            if platform == "youtube" and custom_opts:
                success, msg = downloader.download(url, progress_hooks=[progress_hook], custom_opts=custom_opts)
            else:
                success, msg = downloader.download(url, progress_hooks=[progress_hook])

            if success:
                log.write(f"[bold green]✓ Başarılı:[/bold green] {msg}")
            else:
                log.write(f"[bold red]✗ Hata:[/bold red] {msg}")

        self.run_worker(worker, thread=True)

    def _open_format_picker(self) -> None:
        inp = self.query_one("#input-youtube", Input)
        url = inp.value.strip()
        if not url:
            self.query_one("#log-console", RichLog).write("[bold red]Önce YouTube linkini kutuya yapıştırın![/bold red]")
            return

        def on_modal_result(chosen: dict[str, Any] | None) -> None:
            if not chosen:
                return
            custom_opts = None
            if chosen["type"] == "audio":
                custom_opts = {
                    "format": chosen["format_spec"],
                    "writethumbnail": True,
                    "postprocessors": [
                        {"key": "FFmpegExtractAudio", "preferredcodec": chosen.get("codec", "mp3"), "preferredquality": chosen.get("quality", "320")},
                        {"key": "FFmpegMetadata", "add_metadata": True},
                        {"key": "EmbedThumbnail", "already_have_thumbnail": False},
                    ],
                }
            else:
                custom_opts = {
                    "format": chosen["format_spec"],
                    "merge_output_format": "mp4",
                }
            self._start_single_download("youtube", custom_opts=custom_opts)

        self.push_screen(FormatPickerModal(url, cookies_file=self.config.cookies_file), on_modal_result)

    def _start_mp3_download(self) -> None:
        custom_opts = {
            "format": "bestaudio/best",
            "writethumbnail": True,
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "320"},
                {"key": "FFmpegMetadata", "add_metadata": True},
                {"key": "EmbedThumbnail", "already_have_thumbnail": False},
            ],
        }
        self._start_single_download("youtube", custom_opts=custom_opts)

    def _open_search_modal(self) -> None:
        def on_search_result(url: str | None) -> None:
            if url:
                inp = self.query_one("#input-youtube", Input)
                inp.value = url
                self._start_single_download("youtube")

        self.push_screen(SearchModal(self.downloaders["youtube"]), on_search_result)

    def _start_auto_scan(self, platform: str) -> None:
        log = self.query_one("#log-console", RichLog)
        downloads = Path(os.path.expanduser("~")) / "Downloads"
        candidates = sorted(downloads.glob("*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
        valid = [c for c in candidates if "cookie" not in c.name.lower()]

        if not valid:
            log.write("[bold red]İndirilenler klasöründe geçerli bir .txt URL listesi bulunamadı![/bold red]")
            return

        target_file = str(valid[0])
        log.write(f"[green]Otomatik bulunan liste:[/green] [bold]{valid[0].name}[/bold]")
        self._execute_bulk(platform, target_file)

    def _prompt_bulk_file(self, platform: str) -> None:
        def on_file_selected(file_path: str | None) -> None:
            if file_path:
                self._execute_bulk(platform, file_path)

        self.push_screen(FilePromptModal(f"{platform.upper()} Toplu İndirme Dosya Yolu:"), on_file_selected)

    def _execute_bulk(self, platform: str, file_path: str) -> None:
        def worker():
            log = self.query_one("#log-console", RichLog)
            log.write(f"\n[bold cyan]Toplu İndirme Başlatılıyor ({platform.upper()}):[/bold cyan] {file_path}")
            downloader = self.downloaders.get(platform)
            if not downloader:
                return

            def progress_cb(curr, tot, u, ok, m):
                self.call_from_thread(
                    log.write,
                    f"[{curr}/{tot}] {u[:45]}... -> {'[green]Tamamlandı[/green]' if ok else f'[red]Hata: {m}[/red]'}"
                )
                pb = self.query_one("#global-progress", ProgressBar)
                self.call_from_thread(pb.update, progress=(curr / tot) * 100)

            succ, fail, skip, failed_urls = downloader.bulk_download_from_file(file_path, progress_callback=progress_cb)
            log.write(f"\n[bold green]Toplu İndirme Özeti:[/bold green] Başarılı: {succ} | Hatalı: {fail} | Atlanan: {skip}")

        self.run_worker(worker, thread=True)

    # =========================================================================
    # SPECIALIZED PLATFORM OPERATIONS
    # =========================================================================
    def _start_library_download(self) -> None:
        self._prompt_bulk_file("youtube")

    def _start_tiktok_liked(self) -> None:
        self._prompt_bulk_file("tiktok")

    def _start_tiktok_favs(self) -> None:
        self._prompt_bulk_file("tiktok")

    def _start_tiktok_export(self) -> None:
        def on_export_file(file_path: str | None) -> None:
            if not file_path:
                return
            log = self.query_one("#log-console", RichLog)
            try:
                tt = self.downloaders["tiktok"]
                urls = tt.read_liked_from_json(file_path)
                log.write(f"[green]JSON Export'tan {len(urls)} adet video çıkarıldı![/green]")
                self.run_worker(lambda: tt.bulk_download(urls), thread=True)
            except Exception as e:
                log.write(f"[red]Export okuma hatası:[/red] {e}")

        self.push_screen(FilePromptModal("TikTok Veri Export Dosyası (user_data.json / ZIP):"), on_export_file)

    def _start_twitter_bookmarks(self) -> None:
        self._prompt_bulk_file("twitter")

    # =========================================================================
    # SETTINGS LOGIC
    # =========================================================================
    def _save_settings(self) -> None:
        sel_q = self.query_one("#sel-quality", Select).value
        sel_f = self.query_one("#sel-format", Select).value
        sel_w = self.query_one("#sel-workers", Select).value
        sel_t = self.query_one("#sel-theme", Select).value

        if sel_q: self.config.quality = str(sel_q)
        if sel_f: self.config.format_type = str(sel_f)
        if sel_w: self.config.max_workers = int(sel_w)
        if sel_t: self.config.theme_color = str(sel_t)

        self.config.save()
        log = self.query_one("#log-console", RichLog)
        log.write("[bold green]Ayarlar başarıyla kaydedildi![/bold green]")

    def _reset_settings(self) -> None:
        self.config._set_defaults()
        self.config.save()
        log = self.query_one("#log-console", RichLog)
        log.write("[bold yellow]Ayarlar varsayılana sıfırlandı![/bold yellow]")

    # =========================================================================
    # ACCOUNTS & COOKIES LOGIC
    # =========================================================================
    def _auto_bind_cookies(self) -> None:
        log = self.query_one("#log-console", RichLog)
        downloads = Path(os.path.expanduser("~")) / "Downloads"
        candidates = sorted(downloads.glob("*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
        cookie_files = [c for c in candidates if "cookie" in c.name.lower()]

        if not cookie_files:
            log.write("[bold red]İndirilenler klasöründe cookie dosyası (*cookie*.txt) bulunamadı![/bold red]")
            return

        best = str(cookie_files[0])
        self.config.cookies_file = best
        self.config.auth_method = "cookies_file"
        self.config.twitter_cookies_file = best
        self.config.tiktok_cookies_file = best
        self.config.facebook_cookies_file = best
        self.config.instagram_cookies_file = best
        self.config.pinterest_cookies_file = best
        self.config.save()

        self.query_one(AccountsPane).refresh_table()
        log.write(f"[bold green]Tüm platformlar otomatik olarak çereze bağlandı:[/bold green] {best}")

    def _set_cookie_all(self) -> None:
        inp = self.query_one("#input-cookie-path", Input).value.strip().strip('"').strip("'")
        if not inp or not os.path.exists(inp):
            self.query_one("#log-console", RichLog).write("[bold red]Geçersiz cookie dosya yolu![/bold red]")
            return

        self.config.cookies_file = inp
        self.config.auth_method = "cookies_file"
        self.config.twitter_cookies_file = inp
        self.config.tiktok_cookies_file = inp
        self.config.facebook_cookies_file = inp
        self.config.instagram_cookies_file = inp
        self.config.pinterest_cookies_file = inp
        self.config.save()

        self.query_one(AccountsPane).refresh_table()
        self.query_one("#log-console", RichLog).write(f"[bold green]Çerez tüm platformlara atandı:[/bold green] {inp}")

    def _clear_cookies(self) -> None:
        self.config.cookies_file = None
        self.config.auth_method = None
        self.config.twitter_cookies_file = None
        self.config.tiktok_cookies_file = None
        self.config.facebook_cookies_file = None
        self.config.instagram_cookies_file = None
        self.config.pinterest_cookies_file = None
        self.config.save()

        self.query_one(AccountsPane).refresh_table()
        self.query_one("#log-console", RichLog).write("[bold yellow]Tüm çerez bağlantıları kaldırıldı.[/bold yellow]")

    # =========================================================================
    # AUTOMATION & SERVICES LOGIC
    # =========================================================================
    def _toggle_clipboard_watcher(self) -> None:
        lbl = self.query_one("#lbl-clip-status", Label)
        btn = self.query_one("#btn-toggle-clip", Button)
        if self.clipboard_watcher.is_running:
            self.clipboard_watcher.stop()
            lbl.update("Servis Durumu: [bold yellow]Durduruldu[/bold yellow]")
            btn.label = "Servisi Başlat"
            btn.variant = "success"
        else:
            self.clipboard_watcher.start()
            lbl.update("Servis Durumu: [bold green]Aktif (Çalışıyor)[/bold green]")
            btn.label = "Servisi Durdur"
            btn.variant = "warning"

    def _process_bridge_queue(self) -> None:
        batches = GLOBAL_BRIDGE_QUEUE.get_all_pending()
        log = self.query_one("#log-console", RichLog)
        if not batches:
            log.write("[yellow]Kuyrukta bekleyen URL yok.[/yellow]")
            return

        def worker():
            for b in batches:
                plat = b["platform"]
                urls = b["urls"]
                log.write(f"\n[cyan]Kuyruktan {len(urls)} link indiriliyor ({plat.upper()})...[/cyan]")
                downloader = self.downloaders.get(plat) or self.downloaders["youtube"]
                downloader.bulk_download(urls)

        self.run_worker(worker, thread=True)

    def _add_channel(self) -> None:
        url = self.query_one("#input-watcher-url", Input).value.strip()
        name = self.query_one("#input-watcher-name", Input).value.strip()
        if not url:
            return
        platform = "youtube"
        if "tiktok" in url: platform = "tiktok"
        elif "instagram" in url: platform = "instagram"

        self.channel_watcher.add_target(url, platform, name or url)
        self.query_one("#input-watcher-url", Input).value = ""
        self.query_one("#input-watcher-name", Input).value = ""
        self._load_watcher_table()
        self.query_one("#log-console", RichLog).write(f"[green]Kanal takibe eklendi:[/green] {name or url}")

    def _remove_channel(self) -> None:
        table = self.query_one("#table-channels", DataTable)
        row_idx = table.cursor_row
        targets = self.channel_watcher.list_targets()
        if row_idx is not None and row_idx < len(targets):
            t = targets[row_idx]
            self.channel_watcher.remove_target(t["id"])
            self._load_watcher_table()
            self.query_one("#log-console", RichLog).write(f"[yellow]Kanal takipten çıkarıldı:[/yellow] {t['name']}")

    def _scan_all_channels(self) -> None:
        def worker():
            log = self.query_one("#log-console", RichLog)
            targets = self.channel_watcher.list_targets()
            if not targets:
                log.write("[yellow]Takip edilen kanal yok.[/yellow]")
                return

            all_new = []
            for t in targets:
                log.write(f"[dim]Taranıyor: {t['name']}...[/dim]")
                vids = self.channel_watcher.scan_target_for_new_videos(t, limit=5)
                if vids:
                    log.write(f"[green]+ {len(vids)} yeni video bulundu![/green]")
                    all_new.extend(vids)

            if all_new:
                log.write(f"[bold green]Toplam {len(all_new)} yeni video indiriliyor...[/bold green]")
                self.downloaders["youtube"].bulk_download(all_new)
            else:
                log.write("[dim]Yeni video bulunamadı.[/dim]")

        self.run_worker(worker, thread=True)

    def _load_watcher_table(self) -> None:
        try:
            table = self.query_one("#table-channels", DataTable)
            table.clear()
            for t in self.channel_watcher.list_targets():
                table.add_row(t.get("id", "-"), t.get("name", "-"), t.get("platform", "-"), t.get("url", "-"))
        except Exception:
            pass

    # =========================================================================
    # HISTORY LOGIC
    # =========================================================================
    def _load_history_table(self) -> None:
        try:
            table = self.query_one("#table-history", DataTable)
            table.clear()
            history = self.downloaders["youtube"].history._history
            for plat, vids in history.items():
                for vid_id, data in vids.items():
                    date = data.get("date", "-")
                    url = data.get("url", "-")
                    table.add_row(plat.upper(), vid_id, date, url)
        except Exception:
            pass

    def _clear_history(self) -> None:
        yt_history = self.downloaders["youtube"].history
        for p in yt_history.PLATFORMS:
            yt_history._history[p] = {}
        yt_history.save_history()
        self._load_history_table()
        self.query_one("#log-console", RichLog).write("[bold yellow]İndirme geçmişi temizlendi.[/bold yellow]")

    def on_unmount(self) -> None:
        self.bridge_server.stop()
        self.clipboard_watcher.stop()
