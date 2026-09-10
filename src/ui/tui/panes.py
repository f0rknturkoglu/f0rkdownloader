"""
TUI Panes Module
Contains individual view panels for Platforms, Automation Services,
Settings, Account Management, and Download History.
"""

import os
import subprocess
from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    DataTable,
    Input,
    Label,
    OptionList,
    Select,
    Static,
)

from src.config import Config


def open_folder_in_file_manager(path: str | Path) -> bool:
    """Open folder in system file manager (Windows, Linux, macOS)."""
    p = str(path)
    if not os.path.exists(p):
        os.makedirs(p, exist_ok=True)
    try:
        if os.name == "nt":
            os.startfile(p)
            return True
        elif os.uname().sysname == "Darwin":
            subprocess.Popen(["open", p])
            return True
        else:
            subprocess.Popen(["xdg-open", p])
            return True
    except Exception:
        return False


class PlatformPane(Vertical):
    """View panel for a specific downloader platform."""

    def __init__(self, platform_key: str, platform_title: str, is_video_only: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.platform_key = platform_key
        self.platform_title = platform_title
        self.is_video_only = is_video_only

    def compose(self) -> ComposeResult:
        with Vertical(classes="pane-inner"):
            yield Label(f"[bold cyan]{self.platform_title} İndirici[/bold cyan]", classes="pane-title")

            with Horizontal(classes="url-bar"):
                yield Input(
                    placeholder=f"{self.platform_title} linkini buraya yapıştırın...",
                    id=f"input-{self.platform_key}",
                    classes="main-url-input"
                )

            with Horizontal(classes="action-row"):
                yield Button("İndir", id=f"btn-dl-{self.platform_key}", variant="success")
                if self.platform_key == "youtube":
                    yield Button("Format Seç (İnteraktif)", id=f"btn-fmt-{self.platform_key}", variant="primary")
                    yield Button("Sadece MP3 (320k)", id=f"btn-mp3-{self.platform_key}", variant="warning")
                yield Button("Klasör Tara (Tek Tık)", id=f"btn-scan-{self.platform_key}", variant="default")
                yield Button("Dosyadan Toplu İndir", id=f"btn-bulk-{self.platform_key}", variant="default")

            # Platform specific extras
            if self.platform_key == "youtube":
                with Horizontal(classes="action-row-extra"):
                    yield Button("YouTube'da Ara", id="btn-yt-search", variant="primary")
                    yield Button("Kütüphanem (Playlistler)", id="btn-yt-library", variant="default")
                    yield Button("İndirilenleri Aç", id=f"btn-open-{self.platform_key}", variant="default")
            elif self.platform_key == "tiktok":
                with Horizontal(classes="action-row-extra"):
                    yield Button("Beğenilen Videolar (Liked)", id="btn-tt-liked", variant="default")
                    yield Button("Favori Videolar", id="btn-tt-favs", variant="default")
                    yield Button("TikTok Veri Export (JSON)", id="btn-tt-export", variant="default")
                    yield Button("İndirilenleri Aç", id=f"btn-open-{self.platform_key}", variant="default")
            elif self.platform_key == "twitter":
                with Horizontal(classes="action-row-extra"):
                    yield Button("Yer İmleri (Bookmarks)", id="btn-tw-bookmarks", variant="default")
                    yield Button("İndirilenleri Aç", id=f"btn-open-{self.platform_key}", variant="default")
            else:
                with Horizontal(classes="action-row-extra"):
                    yield Button("İndirilenleri Aç", id=f"btn-open-{self.platform_key}", variant="default")


class SettingsPane(VerticalScroll):
    """View panel for application configuration."""

    def __init__(self, config: Config, **kwargs):
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        yield Label("[bold cyan]Uygulama Ayarları[/bold cyan]", classes="pane-title")

        yield Label("Varsayılan Video Kalitesi:", classes="setting-label")
        yield Select(
            [
                ("En İyi Kalite", "bestvideo+bestaudio/best"),
                ("1080p (Full HD)", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"),
                ("720p (HD)", "bestvideo[height<=720]+bestaudio/best[height<=720]/best"),
                ("En Düşük", "worstvideo+worstaudio/worst"),
            ],
            value=self.config.quality,
            id="sel-quality",
            prompt="Video Kalitesi Seçin"
        )

        yield Label("Varsayılan Format:", classes="setting-label")
        yield Select(
            [
                ("Video (MP4)", "video"),
                ("Sadece Ses (MP3)", "audio"),
            ],
            value=self.config.format_type,
            id="sel-format",
            prompt="Format Seçin"
        )

        yield Label("Eşzamanlı İndirme (İş Parçacığı Sayısı):", classes="setting-label")
        yield Select(
            [
                ("1 (Düşük Sistem / Tekli)", 1),
                ("2 (Dengeli)", 2),
                ("3 (Varsayılan Hızlı)", 3),
                ("4 (Yüksek Hız)", 4),
                ("5 (Maksimum Hız)", 5),
            ],
            value=self.config.max_workers,
            id="sel-workers",
            prompt="İş Parçacığı Seçin"
        )

        yield Label("Uygulama Teması:", classes="setting-label")
        yield Select(
            [
                ("Ubuntu (Vibrant Violet)", "ubuntu"),
                ("Macintosh (Monochrome)", "macintosh"),
                ("Fedora (Accessible Blue)", "fedora"),
            ],
            value=self.config.theme_color,
            id="sel-theme",
            prompt="Tema Seçin"
        )

        yield Label(f"Ana İndirme Klasörü: [bold white]{self.config.download_path}[/bold white]", classes="setting-info")

        with Horizontal(classes="action-row"):
            yield Button("Ayarları Kaydet", id="btn-save-settings", variant="success")
            yield Button("Varsayılana Sıfırla", id="btn-reset-settings", variant="warning")
            yield Button("İndirme Klasörünü Aç", id="btn-open-base-dir", variant="default")


class AccountsPane(VerticalScroll):
    """View panel for account cookies management."""

    def __init__(self, config: Config, **kwargs):
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        yield Label("[bold cyan]Hesap ve Çerez Yönetimi (Cookies)[/bold cyan]", classes="pane-title")

        yield Label("Otomatik Çerez Bağlayıcı:", classes="setting-label")
        yield Label("[dim]İndirilenler klasöründeki güncel cookie.txt dosyasını tek tıkla tüm platformlara bağlar.[/dim]")
        with Horizontal(classes="action-row"):
            yield Button("İndirilenler Klasörünü Tara ve Otomatik Bağla (TEK TIK)", id="btn-auto-cookies", variant="primary")

        yield Label("Platform Çerez Durumları:", classes="setting-label")
        yield DataTable(id="table-cookies")

        yield Label("Manuel Çerez Dosyası Yolu:", classes="setting-label")
        with Horizontal(classes="url-bar"):
            yield Input(placeholder="C:\\Users\\...\\cookies.txt", id="input-cookie-path")

        with Horizontal(classes="action-row"):
            yield Button("Seçili Platforma Ata", id="btn-set-cookie-single", variant="success")
            yield Button("Tüm Platformlara Ata", id="btn-set-cookie-all", variant="warning")
            yield Button("Çerezleri Temizle", id="btn-clear-cookies", variant="error")

    def on_mount(self) -> None:
        table = self.query_one("#table-cookies", DataTable)
        table.cursor_type = "row"
        table.add_columns("Platform", "Durum", "Dosya Yolu")
        self.refresh_table()

    def refresh_table(self) -> None:
        table = self.query_one("#table-cookies", DataTable)
        table.clear()
        platforms = [
            ("YouTube", self.config.cookies_file),
            ("Twitter", self.config.twitter_cookies_file),
            ("TikTok", self.config.tiktok_cookies_file),
            ("Facebook", self.config.facebook_cookies_file),
            ("Instagram", self.config.instagram_cookies_file),
            ("Pinterest", self.config.pinterest_cookies_file),
        ]
        for name, path in platforms:
            status = "[green]Bağlı[/green]" if path and os.path.exists(path) else "[yellow]Bağlı Değil[/yellow]"
            path_str = str(path) if path else "-"
            table.add_row(name, status, path_str)


class ClipboardPane(Vertical):
    """View panel for Clipboard Watcher service."""

    def compose(self) -> ComposeResult:
        yield Label("[bold cyan]Pano İzleme Servisi (Clipboard Watcher)[/bold cyan]", classes="pane-title")
        yield Label("Panoya kopyalanan YouTube, TikTok, Twitter, Facebook, Instagram veya Pinterest linklerini otomatik algılar.", classes="setting-info")

        yield Label("Servis Durumu: [bold green]Aktif (Çalışıyor)[/bold green]", id="lbl-clip-status")

        with Horizontal(classes="action-row"):
            yield Button("Servisi Durdur", id="btn-toggle-clip", variant="warning")
            yield Button("Kuyruktaki Linkleri İndir", id="btn-dl-clip-queue", variant="success")
            yield Button("Listeyi Temizle", id="btn-clear-clip-list", variant="default")

        yield Label("Algılanan ve Kuyruğa Alınan Linkler:", classes="setting-label")
        yield DataTable(id="table-clip-urls")

    def on_mount(self) -> None:
        table = self.query_one("#table-clip-urls", DataTable)
        table.cursor_type = "row"
        table.add_columns("Platform", "URL")


class WatcherPane(Vertical):
    """View panel for Channel and Profile Tracker."""

    def compose(self) -> ComposeResult:
        yield Label("[bold cyan]Kanal ve Profil Takipçisi (Channel Watcher)[/bold cyan]", classes="pane-title")
        yield Label("Favori kanallarınızı ve profillerinizi listeleyin, tek tıkla yeni yayınlanan videoları otomatik arşivleyin.", classes="setting-info")

        with Horizontal(classes="url-bar"):
            yield Input(placeholder="Kanal URL'si (YouTube, TikTok, Instagram)...", id="input-watcher-url")
            yield Input(placeholder="Kanal İsmi...", id="input-watcher-name")
            yield Button("Kanal Ekle", id="btn-add-channel", variant="success")

        with Horizontal(classes="action-row"):
            yield Button("Tüm Kanalları Tara ve Yeni Videoları İndir", id="btn-scan-all-channels", variant="primary")
            yield Button("Seçili Kanalı Sil", id="btn-remove-channel", variant="error")

        yield Label("Takip Edilen Kanallar:", classes="setting-label")
        yield DataTable(id="table-channels")

    def on_mount(self) -> None:
        table = self.query_one("#table-channels", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Kanal Adı", "Platform", "URL")


class BridgePane(Vertical):
    """View panel for Localhost Browser Bridge Server."""

    def compose(self) -> ComposeResult:
        yield Label("[bold cyan]Tarayıcı Köprü Sunucusu (Localhost Bridge :48123)[/bold cyan]", classes="pane-title")
        yield Label(
            "UserScript üzerinden toplanan video linklerini doğrudan bu terminale gönderin.\n"
            "Tampermonkey eklentisindeki '[>] CLI Kuyruğuna Gönder' butonuna basmanız yeterlidir.",
            classes="setting-info"
        )

        yield Label("Köprü Durumu: [bold green]Online (:48123)[/bold green]", id="lbl-bridge-status")
        yield Label("Kuyrukta Bekleyen URL Sayısı: [bold cyan]0[/bold cyan]", id="lbl-bridge-count")

        with Horizontal(classes="action-row"):
            yield Button("Kuyruktaki Tüm Linkleri İndir", id="btn-dl-bridge-queue", variant="success")
            yield Button("Kuyruğu Temizle", id="btn-clear-bridge-queue", variant="default")
            yield Button("Sunucuyu Yeniden Başlat", id="btn-restart-bridge", variant="warning")


class HistoryPane(Vertical):
    """View panel for Download History."""

    def compose(self) -> ComposeResult:
        yield Label("[bold cyan]İndirme Geçmişi (Download History)[/bold cyan]", classes="pane-title")

        with Horizontal(classes="action-row"):
            yield Button("Listeyi Yenile", id="btn-refresh-history", variant="primary")
            yield Button("İndirilenler Klasörünü Aç", id="btn-open-history-dir", variant="default")
            yield Button("Geçmişi Temizle", id="btn-clear-history", variant="error")

        yield Label("İndirilen İçerikler:", classes="setting-label")
        yield DataTable(id="table-history")

    def on_mount(self) -> None:
        table = self.query_one("#table-history", DataTable)
        table.cursor_type = "row"
        table.add_columns("Platform", "Video ID", "Tarih", "URL")
