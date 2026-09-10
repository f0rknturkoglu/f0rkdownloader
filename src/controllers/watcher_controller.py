"""
Automation and Watcher Controller
Handles Clipboard Watcher, Channel Tracker, and Localhost Bridge operations.
"""

from pathlib import Path
from typing import Any

from src.controllers.base import BaseController
from src.utils.bridge import GLOBAL_BRIDGE_QUEUE, LocalBridgeServer
from src.utils.channel_watcher import ChannelWatcher
from src.utils.clipboard_watcher import ClipboardWatcher


class AutomationController(BaseController):
    """Controller for automated watchers and browser bridge."""

    def __init__(self, config: Any, ui: Any, app_controllers: dict[str, Any] | None = None):
        super().__init__(config, ui)
        self.app_controllers = app_controllers or {}
        self.bridge_server = LocalBridgeServer()
        self.channel_watcher = ChannelWatcher(Path(config.base_download_path))
        self.clipboard_watcher = ClipboardWatcher(on_link_found=self._on_clipboard_link)

    def _on_clipboard_link(self, url: str, platform: str) -> None:
        """Called when ClipboardWatcher detects a link."""
        self.ui.console.print(f"\n[bold green][Pano Algılandı - {platform.upper()}][/bold green] {url}")
        # Add to bridge queue for immediate availability
        GLOBAL_BRIDGE_QUEUE.add_batch(platform, [url])

    def run(self) -> None:
        """Main loop for AutomationController."""
        self.ui.push_breadcrumb("Otomasyon Servisleri")

        while True:
            self.ui.print_header(self.config.download_path)

            import questionary
            choices = [
                "Pano İzleme Servisi (Clipboard Watcher)",
                "Kanal ve Profil Takipçisi (Channel Watcher)",
                "Tarayıcı Köprü Sunucusu (Localhost Bridge)",
                "Geri Dön"
            ]

            choice = questionary.select(
                "Otomasyon ve Arka Plan Servisleri:",
                choices=choices,
                style=self.ui.custom_style
            ).ask()

            if not choice or "Geri Dön" in choice:
                break

            if "Pano İzleme" in choice:
                self.run_clipboard_menu()
            elif "Kanal ve Profil" in choice:
                self.run_channel_menu()
            elif "Tarayıcı Köprü" in choice:
                self.run_bridge_menu()

        self.ui.pop_breadcrumb()

    def run_clipboard_menu(self) -> None:
        """Menu for Clipboard Watcher."""
        self.ui.push_breadcrumb("Pano İzleyici")

        while True:
            self.ui.print_header(self.config.download_path)
            status_text = "[green]Aktif (Çalışıyor)[/green]" if self.clipboard_watcher.is_running else "[yellow]Durduruldu[/yellow]"
            self.ui.console.print(f"\nDurum: {status_text}\n")

            import questionary
            choices = [
                "Servisi Başlat" if not self.clipboard_watcher.is_running else "Servisi Durdur",
                "Kuyruktaki Linkleri İndir",
                "Geri Dön"
            ]

            choice = questionary.select(
                "Pano İzleme İşlemleri:",
                choices=choices,
                style=self.ui.custom_style
            ).ask()

            if not choice or "Geri Dön" in choice:
                break

            if "Servisi Başlat" in choice:
                success = self.clipboard_watcher.start()
                if success:
                    self.ui.show_success("Pano izleyici arka planda başlatıldı. Kopyaladığınız linkler otomatik algılanacak.")
                else:
                    self.ui.show_error("Pano izleyici başlatılamadı (pyperclip modülü eksik olabilir).")
                self.ui.wait_for_enter()
            elif "Servisi Durdur" in choice:
                self.clipboard_watcher.stop()
                self.ui.show_info("Pano izleyici durduruldu.")
                self.ui.wait_for_enter()
            elif "Kuyruktaki" in choice:
                self.handle_process_queue()

        self.ui.pop_breadcrumb()

    def run_channel_menu(self) -> None:
        """Menu for Channel and Profile Tracker."""
        self.ui.push_breadcrumb("Kanal Takipçisi")

        while True:
            self.ui.print_header(self.config.download_path)
            targets = self.channel_watcher.list_targets()
            self.ui.console.print(f"\nTakip Edilen Kanal Sayısı: [bold]{len(targets)}[/bold]\n")

            import questionary
            choices = [
                "Tüm Kanalları Tara ve Yeni Videoları İndir",
                "Yeni Kanal / Profil Ekle",
                "Takip Listesini Görüntüle / Sil",
                "Geri Dön"
            ]

            choice = questionary.select(
                "Kanal Takip İşlemleri:",
                choices=choices,
                style=self.ui.custom_style
            ).ask()

            if not choice or "Geri Dön" in choice:
                break

            if "Tüm Kanalları Tara" in choice:
                self.handle_scan_channels()
            elif "Yeni Kanal" in choice:
                self.handle_add_channel()
            elif "Listesini Görüntüle" in choice:
                self.handle_manage_channels()

        self.ui.pop_breadcrumb()

    def run_bridge_menu(self) -> None:
        """Menu for Browser Localhost Bridge Server."""
        self.ui.push_breadcrumb("Tarayıcı Köprüsü")

        while True:
            self.ui.print_header(self.config.download_path)
            status_text = "[green]Açık (Port: 48123)[/green]" if self.bridge_server.is_running else "[yellow]Kapalı[/yellow]"
            pending_count = GLOBAL_BRIDGE_QUEUE.total_count
            self.ui.console.print(f"\nKöprü Durumu: {status_text} | Bekleyen URL: [bold cyan]{pending_count}[/bold cyan]\n")

            import questionary
            choices = [
                "Köprü Sunucusunu Başlat" if not self.bridge_server.is_running else "Köprü Sunucusunu Durdur",
                f"Kuyruktaki Linkleri İndir ({pending_count} adet)",
                "Geri Dön"
            ]

            choice = questionary.select(
                "Tarayıcı Köprüsü İşlemleri:",
                choices=choices,
                style=self.ui.custom_style
            ).ask()

            if not choice or "Geri Dön" in choice:
                break

            if "Sunucusunu Başlat" in choice:
                if self.bridge_server.start():
                    self.ui.show_success("Köprü sunucusu 127.0.0.1:48123 üzerinde başlatıldı. UserScript'ten 'CLI Kuyruğuna Gönder' butonunu kullanabilirsiniz.")
                else:
                    self.ui.show_error("Köprü sunucusu başlatılamadı.")
                self.ui.wait_for_enter()
            elif "Sunucusunu Durdur" in choice:
                self.bridge_server.stop()
                self.ui.show_info("Köprü sunucusu durduruldu.")
                self.ui.wait_for_enter()
            elif "Kuyruktaki" in choice:
                self.handle_process_queue()

        self.ui.pop_breadcrumb()

    def handle_process_queue(self) -> None:
        """Download all URLs in the bridge queue."""
        batches = GLOBAL_BRIDGE_QUEUE.get_all_pending()
        if not batches:
            self.ui.show_info("Kuyrukta bekleyen link yok.")
            self.ui.wait_for_enter()
            return

        total_urls = sum(len(b["urls"]) for b in batches)
        self.ui.console.print(f"\n[bold cyan]Kuyruktaki {total_urls} adet link indirilmeye başlanıyor...[/bold cyan]\n")

        for b in batches:
            platform = b["platform"]
            urls = b["urls"]
            controller = self.app_controllers.get(platform)
            if controller and hasattr(controller, "downloader"):
                controller.downloader.bulk_download(urls, progress_callback=self.ui.show_progress)
            else:
                yt_controller = self.app_controllers.get("youtube")
                if yt_controller and hasattr(yt_controller, "downloader"):
                    yt_controller.downloader.bulk_download(urls, progress_callback=self.ui.show_progress)

        self.ui.show_success(f"Kuyruktaki {total_urls} linkin indirme işlemi tamamlandı.")
        self.ui.wait_for_enter()

    def handle_add_channel(self) -> None:
        import questionary
        url = questionary.text("Kanal / Profil URL:", style=self.ui.custom_style).ask()
        if not url:
            return
        platform = "youtube"
        if "tiktok" in url:
            platform = "tiktok"
        elif "instagram" in url:
            platform = "instagram"

        name = questionary.text("Kanal İsmi (İsteğe bağlı):", style=self.ui.custom_style).ask() or url
        self.channel_watcher.add_target(url, platform, name)
        self.ui.show_success(f"Kanal takip listesine eklendi: {name}")
        self.ui.wait_for_enter()

    def handle_manage_channels(self) -> None:
        targets = self.channel_watcher.list_targets()
        if not targets:
            self.ui.show_info("Henüz takip edilen kanal yok.")
            self.ui.wait_for_enter()
            return

        import questionary
        choices = [f"[{t['platform'].upper()}] {t['name']}" for t in targets]
        choices.append("İptal")

        sel = questionary.select("Silmek istediğiniz kanalı seçin:", choices=choices, style=self.ui.custom_style).ask()
        if not sel or sel == "İptal":
            return

        idx = choices.index(sel)
        target = targets[idx]
        self.channel_watcher.remove_target(target["id"])
        self.ui.show_success(f"Kanal silindi: {target['name']}")
        self.ui.wait_for_enter()

    def handle_scan_channels(self) -> None:
        targets = self.channel_watcher.list_targets()
        if not targets:
            self.ui.show_info("Takip edilen kanal bulunamadı. Önce bir kanal ekleyin.")
            self.ui.wait_for_enter()
            return

        all_new_videos = []
        for target in targets:
            self.ui.console.print(f"[dim]Taranıyor: {target['name']}...[/dim]")
            new_vids = self.channel_watcher.scan_target_for_new_videos(target, limit=5)
            if new_vids:
                self.ui.console.print(f"[green]+ {len(new_vids)} yeni video bulundu![/green]")
                all_new_videos.extend(new_vids)

        if all_new_videos:
            self.ui.console.print(f"\n[bold green]Toplam {len(all_new_videos)} yeni video indiriliyor...[/bold green]\n")
            yt_controller = self.app_controllers.get("youtube")
            if yt_controller:
                yt_controller.downloader.bulk_download(all_new_videos, progress_callback=self.ui.show_progress)
            self.ui.show_success("Tüm yeni videolar indirildi!")
        else:
            self.ui.show_info("Kanallarda yeni bir video bulunamadı.")

        self.ui.wait_for_enter()
