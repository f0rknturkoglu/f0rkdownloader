"""
YouTube Controller
Handles all YouTube-related UI operations.
"""

import os
import sys
from typing import Any

from src.controllers.base import BaseController
from src.core.youtube import YoutubeDownloader
from src.core.format_selector import FormatSelector


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
                elif "Tara ve Toplu İndir" in choice:
                    self.handle_auto_scan()
                elif "Toplu İndir" in choice:
                    self.handle_bulk_download()
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
        """Handle link-based download with interactive quality/format options."""
        import questionary
        url = self.ui.console.input("\n[bold cyan]YouTube URL (Video veya Playlist):[/bold cyan] ").strip()
        if not url:
            return

        mode_choices = [
            "⚡ Hızlı İndir (Varsayılan Kalite)",
            "🎬 Çözünürlük ve Format Seç (İnteraktif)",
            "🎵 Sadece MP3 İndir (320 kbps + Albüm Kapağı & Metadata)",
            "İptal"
        ]

        mode = questionary.select(
            "İndirme Modu:",
            choices=mode_choices,
            style=self.ui.custom_style
        ).ask()

        if not mode or mode == "İptal":
            return

        custom_opts = None

        if "İnteraktif" in mode:
            self.ui.console.print("\n[dim]Mevcut çözünürlükler ve formatlar taranıyor...[/dim]")
            try:
                format_info = FormatSelector.extract_available_formats(
                    url, cookies_file=self.config.cookies_file
                )
                choices_map = {c["label"]: c for c in format_info["choices"]}
                choices_map["İptal"] = None

                chosen_label = questionary.select(
                    f"Format Seçin [{format_info['title'][:50]}...]:",
                    choices=list(choices_map.keys()),
                    style=self.ui.custom_style
                ).ask()

                if not chosen_label or chosen_label == "İptal":
                    return

                selected_opt = choices_map[chosen_label]
                if selected_opt["type"] == "audio":
                    custom_opts = {
                        "format": selected_opt["format_spec"],
                        "writethumbnail": True,
                        "postprocessors": [
                            {
                                "key": "FFmpegExtractAudio",
                                "preferredcodec": selected_opt.get("codec", "mp3"),
                                "preferredquality": selected_opt.get("quality", "320"),
                            },
                            {
                                "key": "FFmpegMetadata",
                                "add_metadata": True,
                            },
                            {
                                "key": "EmbedThumbnail",
                                "already_have_thumbnail": False,
                            },
                        ],
                    }
                else:
                    custom_opts = {
                        "format": selected_opt["format_spec"],
                        "merge_output_format": "mp4",
                    }
            except Exception as e:
                self.ui.show_warning(f"Format listesi alınamadı ({e}), varsayılan ayarlarla devam ediliyor.")

        elif "Sadece MP3" in mode:
            custom_opts = {
                "format": "bestaudio/best",
                "writethumbnail": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "320",
                    },
                    {
                        "key": "FFmpegMetadata",
                        "add_metadata": True,
                    },
                    {
                        "key": "EmbedThumbnail",
                        "already_have_thumbnail": False,
                    },
                ],
            }

        self.ui.console.print(f"\n[bold green]İndiriliyor...[/bold green] [dim]{url}[/dim]\n")
        self.logger.download_start("youtube", url)

        success, message = self.downloader.download(url, custom_opts=custom_opts)

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
        from src.core.auth import AuthManager
        auth_mgr = AuthManager(self.config)
        if not self.config.auth_method:
            self.ui.show_error("Kütüphanenizdeki playlistleri görmek için önce Hesap İşlemleri menüsünden giriş yapmalısınız.")
            self.ui.wait_for_enter()
            return
            
        self.ui.console.print("\n[dim]Kütüphane taranıyor...[/dim]")
        playlists = auth_mgr.get_user_playlists()
        if not playlists:
            self.ui.show_warning("Kütüphanenizde oynatma listesi bulunamadı veya oturumunuz geçersiz.")
            self.ui.wait_for_enter()
            return

        import questionary
        choices = [f"{p.get('title', 'İsimsiz')} | {p.get('url', '')}" for p in playlists if p.get('url')]
        choices.append("Geri Dön")
        selected = questionary.select(
            "Hangi playlisti indirmek istersiniz?",
            choices=choices,
            style=self.ui.custom_style
        ).ask()
        if not selected or selected == "Geri Dön":
            return
            
        idx = choices.index(selected)
        target_playlist = playlists[idx]
        self.ui.console.print(f"\n[bold green]Playlist indiriliyor:[/bold green] {target_playlist.get('title')}\n")
        success, message = self.downloader.download(target_playlist.get('url'))
        if success:
            self.ui.show_success(message)
        else:
            self.ui.show_error(message)
        self.ui.wait_for_enter()

    def _execute_bulk(self, file_path: str) -> None:
        """Execute bulk download from given file path."""
        self.ui.print_header(self.config.download_path)

        try:
            urls = self.downloader.read_urls_from_file(file_path)
            if not urls:
                self.ui.show_warning("Dosyada geçerli YouTube URL'si bulunamadı!")
                self.ui.wait_for_enter()
                return

            self.ui.console.print(
                f"\n[bold cyan]Toplu İndirme Başlıyor[/bold cyan]\n"
                f"[dim]Dosya: {file_path}[/dim]\n"
                f"[dim]Toplam URL: {len(urls)}[/dim]\n"
            )
            self.logger.info(f"YouTube bulk download: {len(urls)} URLs from {file_path}")

            successful, failed, skipped, failed_urls = self.downloader.bulk_download(
                urls,
                progress_callback=self.ui.show_progress,
            )

            self.ui.show_summary(successful, failed, failed_urls, skipped)
            self.logger.info(f"YouTube bulk complete: success={successful}, failed={failed}, skipped={skipped}")

        except FileNotFoundError as e:
            self.ui.show_error(str(e))
        except Exception as e:
            self.handle_error(e, "YouTube bulk download")

        self.ui.wait_for_enter()

    def handle_auto_scan(self) -> None:
        """1-Click scan Downloads folder and download YouTube videos."""
        self.auto_scan_and_bulk_download("YouTube", "youtube", self._execute_bulk)

    def handle_bulk_download(self) -> None:
        """Download multiple YouTube videos with picker."""
        file_path = self.prompt_url_list_file("YouTube", keyword="youtube")
        if not file_path:
            return
        self._execute_bulk(file_path)

    def handle_manage_downloads(self) -> None:
        """Open download folder."""
        path = self.downloader.youtube_path
        self.ui.show_info(f"İndirilenler burada: {path}")
        if os.name == 'nt':
            os.startfile(path)
        elif sys.platform == 'darwin':
            import subprocess
            subprocess.run(['open', str(path)])
        else:
            import subprocess
            subprocess.run(['xdg-open', str(path)])
        self.ui.wait_for_enter()
