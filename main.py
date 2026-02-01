import questionary
from pathlib import Path
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
)

from src.config import Config
from src.ui.interface import Interface
from src.ui.theme import custom_style
from src.core.youtube import YoutubeDownloader
from src.core.twitter import TwitterDownloader
from src.core.auth import AuthManager
from src.utils.file_ops import FileManager


class Application:
    def __init__(self):
        self.config = Config()
        self.ui = Interface()
        self.auth_manager = AuthManager(self.config)
        self.downloader = YoutubeDownloader(self.config)
        self.twitter_downloader = TwitterDownloader(self.config)
        self.file_manager = FileManager(self.config.download_path)

        # Downloads klasörü
        self.downloads_folder = Path.home() / "Downloads"

    def _get_cookie_files(self) -> list[dict]:
        """Downloads klasöründeki potansiyel cookie dosyalarını listele."""
        cookie_files = []

        if not self.downloads_folder.exists():
            return cookie_files

        # .txt dosyalarını tara
        for file in self.downloads_folder.glob("*.txt"):
            try:
                # Dosya boyutunu kontrol et (cookie dosyaları genellikle küçüktür)
                size = file.stat().st_size
                if size > 0 and size < 1024 * 1024:  # 1MB'den küçük
                    # İlk birkaç satırı oku ve Netscape format mı kontrol et
                    with open(file, "r", encoding="utf-8", errors="ignore") as f:
                        first_lines = f.read(500)

                    # Netscape cookie formatı veya bilinen cookie içerikleri
                    is_cookie = (
                        "# Netscape HTTP Cookie File" in first_lines or
                        "# HTTP Cookie File" in first_lines or
                        ".twitter.com" in first_lines or
                        ".x.com" in first_lines or
                        ".youtube.com" in first_lines or
                        "auth_token" in first_lines or
                        "ct0" in first_lines
                    )

                    if is_cookie:
                        # Platform tespiti
                        platform = "Bilinmeyen"
                        if ".twitter.com" in first_lines or ".x.com" in first_lines or "ct0" in first_lines:
                            platform = "Twitter/X"
                        elif ".youtube.com" in first_lines:
                            platform = "YouTube"

                        cookie_files.append({
                            "path": str(file),
                            "name": file.name,
                            "size": size,
                            "platform": platform,
                        })
            except (OSError, IOError):
                continue

        return cookie_files

    def _select_cookie_file(self, platform: str = "Cookie") -> str | None:
        """Downloads klasöründen cookie dosyası seç."""
        cookie_files = self._get_cookie_files()

        if not cookie_files:
            self.ui.console.print(
                "[yellow]Downloads klasöründe cookie dosyası bulunamadı.[/yellow]\n"
                "[dim]Tarayıcı eklentisi ile cookie export edin ve Downloads'a kaydedin.[/dim]"
            )
            # Manuel giriş seçeneği sun
            manual = questionary.confirm(
                "Manuel olarak dosya yolu girmek ister misiniz?",
                default=False,
                style=custom_style,
            ).ask()

            if manual:
                path = questionary.text(
                    "Cookie dosya yolu:",
                    style=custom_style,
                ).ask()
                return path.strip().strip('"').strip("'") if path else None
            return None

        # Cookie dosyalarını listele
        choices = ["🔙 İptal"]

        for cf in cookie_files:
            size_kb = cf["size"] / 1024
            label = f"📄 {cf['name']} ({cf['platform']}, {size_kb:.1f} KB)"
            choices.append(label)

        choices.append("📝 Manuel Giriş")

        self.ui.console.print(
            "\n[bold]Downloads klasöründe bulunan cookie dosyaları:[/bold]"
        )

        selected = questionary.select(
            f"{platform} için cookie dosyası seçin:",
            choices=choices,
            style=custom_style,
        ).ask()

        if not selected or "İptal" in selected:
            return None

        if "Manuel Giriş" in selected:
            path = questionary.text(
                "Cookie dosya yolu:",
                style=custom_style,
            ).ask()
            return path.strip().strip('"').strip("'") if path else None

        # Seçilen dosyayı bul
        for cf in cookie_files:
            if cf["name"] in selected:
                return cf["path"]

        return None

    def _show_connection_status(self):
        """Oturum durumunu göster."""
        status_parts = []

        # YouTube durumu
        if self.config.auth_method:
            yt_name = self.config.channel_name or "Bağlı"
            status_parts.append(f"[red]YouTube[/red]: {yt_name}")

        # Twitter durumu
        if self.config.twitter_cookies_file:
            tw_name = self.config.twitter_username or "Bağlı"
            status_parts.append(f"[cyan]Twitter[/cyan]: @{tw_name}")

        if status_parts:
            status_text = " │ ".join(status_parts)
            self.ui.console.print(
                f"[green]●[/green] {status_text}",
                justify="center",
            )
        else:
            self.ui.console.print(
                "[dim]○ Misafir Modu - Hesap İşlemlerinden bağlanabilirsiniz[/dim]",
                justify="center",
            )
        self.ui.console.print()  # Boşluk

    def _get_file_stats(self) -> dict:
        """İndirilen dosya istatistiklerini döndür."""
        files = self.file_manager.get_all_files()
        return {"total": len(files)}

    def run(self):
        """Ana uygulama döngüsü."""
        while True:
            try:
                # Breadcrumb temizle (ana menüye döndük)
                self.ui.clear_breadcrumb()

                self.ui.print_header(self.config.download_path)
                self._show_connection_status()

                # Dosya istatistiklerini al
                stats = self._get_file_stats()

                choice = self.ui.ask_main_menu(stats)

                if not choice:  # Ctrl+C veya ESC
                    break

                if "Link ile İndir" in choice:
                    self.handle_download()
                elif "YouTube'da Ara" in choice:
                    self.handle_search()
                elif "Kütüphanemden İndir" in choice:
                    self.handle_library_download()
                elif "Twitter/X" in choice:
                    self.handle_twitter_download()
                elif "İndirilenleri Yönet" in choice:
                    self.handle_downloads_manager()
                elif "Hesap İşlemleri" in choice:
                    self.handle_account_setup()
                elif "Ayarlar" in choice:
                    self.handle_settings()
                elif "Çıkış" in choice:
                    break

            except KeyboardInterrupt:
                # Ctrl+C yakalandı - ana menüye dön
                continue

        # Çıkış mesajı
        self.ui.clear_screen()
        self.ui.console.print(
            "[bold cyan]Görüşmek üzere! 👋[/bold cyan]",
            justify="center",
        )

    def handle_downloads_manager(self):
        """İndirilen dosyaları yönet."""
        self.ui.push_breadcrumb("İndirilenler")

        while True:
            # Ağacı göster
            tree = self.file_manager.get_tree()
            self.ui.show_file_tree(tree)

            # Dosyaları listele
            files = self.file_manager.get_all_files()
            if not files:
                self.ui.show_warning("Henüz hiç dosya indirilmemiş.")
                self.ui.wait_for_enter("Menüye dönmek için Enter...")
                break

            # Kullanıcıdan seçim iste
            selected = self.ui.ask_file_to_open(files)

            if not selected or "Geri Dön" in selected:
                break

            # İşlem seçimi (Aç veya Sil)
            action = self.ui.ask_file_action(selected)

            if not action or "İptal" in action:
                continue

            if "Aç/Oynat" in action:
                # Dosyayı aç
                success, msg = self.file_manager.open_file(selected)
                if success:
                    self.ui.show_success(msg)
                else:
                    self.ui.show_error(f"Dosya açılamadı: {msg}")
                    self.ui.wait_for_enter()

            elif "Sil" in action:
                if self.ui.ask_confirmation(f"{selected} silinecek. Emin misiniz?"):
                    success, msg = self.file_manager.delete_file(selected)
                    if success:
                        self.ui.show_success(msg)
                        self.ui.wait_for_enter()
                    else:
                        self.ui.show_error(f"Dosya silinemedi: {msg}")
                        self.ui.wait_for_enter()

        self.ui.pop_breadcrumb()

    def handle_account_setup(self):
        """Hesap bağlantı işlemleri."""
        self.ui.push_breadcrumb("Hesap İşlemleri")
        self.ui.print_header(self.config.download_path)

        # Mevcut bağlantı durumlarını göster
        yt_connected = bool(self.config.auth_method)
        tw_connected = bool(self.config.twitter_cookies_file)

        if yt_connected or tw_connected:
            self.ui.console.print("\n[bold]Mevcut Bağlantılar:[/bold]")
            if yt_connected:
                yt_name = self.config.channel_name or "Bağlı"
                self.ui.console.print(
                    f"  [green]●[/green] [red]YouTube[/red]: {yt_name}")
            if tw_connected:
                tw_name = self.config.twitter_username or "Bağlı"
                self.ui.console.print(
                    f"  [green]●[/green] [cyan]Twitter[/cyan]: @{tw_name}")
            self.ui.console.print("")

        # Yöntem Seçimi
        auth_choice = self.ui.ask_auth_method(yt_connected, tw_connected)

        if not auth_choice or "Geri Dön" in auth_choice:
            self.ui.pop_breadcrumb()
            return

        if "YouTube Cookie ile Bağlan" in auth_choice:
            self._handle_youtube_cookie_login()

        elif "YouTube Tarayıcı Çerezleri" in auth_choice:
            browser = self.ui.ask_browser()
            if browser:
                if self.auth_manager.validate_browser_cookies(browser):
                    self.ui.show_success(
                        f"YouTube'a giriş yapıldı! ({browser})")
                else:
                    self.ui.show_error(
                        f"{browser} üzerinden oturum açılamadı.\n"
                        "Windows'ta 'Cookie Dosyası' yöntemini deneyin."
                    )
                self.ui.wait_for_enter()

        elif "Twitter/X Cookie ile Bağlan" in auth_choice:
            self._handle_twitter_cookie_login()

        elif "YouTube Oturumunu Kapat" in auth_choice:
            self.auth_manager.logout()
            self.ui.show_success("YouTube oturumu kapatıldı.")
            self.ui.wait_for_enter()

        elif "Twitter Oturumunu Kapat" in auth_choice:
            self.config.twitter_cookies_file = None
            self.config.twitter_username = None
            self.ui.show_success("Twitter oturumu kapatıldı.")
            self.ui.wait_for_enter()

        elif "Tüm Oturumları Kapat" in auth_choice:
            self.auth_manager.logout()
            self.config.twitter_cookies_file = None
            self.config.twitter_username = None
            self.ui.show_success("Tüm oturumlar kapatıldı.")
            self.ui.wait_for_enter()

        self.ui.pop_breadcrumb()

    def _handle_youtube_cookie_login(self):
        """YouTube için cookie dosyası ile giriş."""
        self.ui.console.print("\n[bold red]YouTube Cookie Girişi[/bold red]")
        self.ui.console.print(
            "[dim]youtube.com'dan export edilmiş cookie dosyası gerekli[/dim]\n")

        cookies_file = self._select_cookie_file("YouTube")
        if not cookies_file:
            return

        self.ui.console.print("[yellow]YouTube kontrol ediliyor...[/yellow]")
        if self.auth_manager.validate_cookies_file(cookies_file):
            yt_name = self.config.channel_name or "Bilinmeyen"
            self.ui.show_success(f"YouTube bağlandı: {yt_name}")
        else:
            self.ui.show_error(
                "YouTube'a bağlanılamadı. Cookie dosyasını kontrol edin.")

        self.ui.wait_for_enter()

    def _handle_twitter_cookie_login(self):
        """Twitter için cookie dosyası ile giriş."""
        self.ui.console.print(
            "\n[bold cyan]Twitter/X Cookie Girişi[/bold cyan]")
        self.ui.console.print(
            "[dim]x.com'dan export edilmiş cookie dosyası gerekli[/dim]")
        self.ui.console.print(
            "[dim]Cookie'de 'ct0' ve 'auth_token' olmalı[/dim]\n")

        cookies_file = self._select_cookie_file("Twitter")
        if not cookies_file:
            return

        self.ui.console.print("[yellow]Twitter kontrol ediliyor...[/yellow]")

        success, error_msg = self.twitter_downloader.validate_twitter_cookies(
            cookies_file)
        if success:
            self.ui.show_success("Twitter bağlandı!")
        else:
            self.ui.show_error(
                f"Twitter'a bağlanılamadı.\n"
                f"Hata: {error_msg}\n\n"
                f"Cookie dosyasının x.com'dan alındığından emin olun."
            )

        self.ui.wait_for_enter()

    def _fetch_twitter_username(self):
        """Twitter kullanıcı adını almaya çalış."""
        # Şimdilik basit bir şekilde None bırakıyoruz
        # İleride Twitter API ile alınabilir
        self.config.twitter_username = None

    def handle_library_download(self):
        """Kütüphaneden playlist indirme."""
        self.ui.push_breadcrumb("Kütüphane")
        self.ui.print_header(self.config.download_path)

        if not self.config.auth_method:
            self.ui.show_error("Bu özellik için önce oturum açmalısınız.")
            self.ui.wait_for_enter("Menüye dönmek için Enter...")
            self.ui.pop_breadcrumb()
            return

        self.ui.console.print(
            "[yellow]Kütüphaneniz taranıyor... (Bu işlem birkaç saniye sürebilir)[/yellow]"
        )

        playlists = self.auth_manager.get_user_playlists()

        if not playlists:
            self.ui.show_error(
                "Playlist bulunamadı veya erişilemedi.\nLütfen 'Hesap İşlemleri'nden tekrar giriş yapmayı deneyin."
            )
            self.ui.wait_for_enter()
            self.ui.pop_breadcrumb()
            return

        selection = self.ui.ask_playlist_selection(playlists)

        if not selection or "Geri Dön" in selection:
            self.ui.pop_breadcrumb()
            return

        # Seçilen "Title | URL" formatından URL'yi ayıkla
        url = selection.split("|")[-1].strip()
        self.perform_download(url)
        self.ui.pop_breadcrumb()

    def handle_download(self):
        url = self.ui.ask_url()
        if not url:
            return
        self.perform_download(url)

    def handle_twitter_download(self):
        """Twitter/X video indirme işlemlerini yönetir."""
        self.ui.push_breadcrumb("Twitter/X")

        while True:
            self.ui.print_header(self.config.download_path)

            # Twitter oturum durumunu göster
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

            has_cookies = bool(self.config.twitter_cookies_file)
            choice = self.ui.ask_twitter_menu(has_cookies)

            if not choice or "Geri Dön" in choice:
                break

            if "Bookmarks" in choice:
                self._handle_twitter_bookmarks()
            elif "Tek Link" in choice:
                self._handle_twitter_single()
            elif "Toplu İndir" in choice:
                self._handle_twitter_bulk()

        self.ui.pop_breadcrumb()

    def _handle_twitter_bookmarks(self):
        """Twitter bookmarks'ları indirir."""
        self.ui.console.print(
            "\n[bold cyan]Bookmarks taranıyor...[/bold cyan]\n"
        )

        bookmarks = self.twitter_downloader.get_bookmarks()

        if not bookmarks:
            self.ui.show_error(
                "Bookmark bulunamadı veya erişilemedi.\n"
                "Cookie dosyanızın geçerli olduğundan emin olun."
            )
            self.ui.wait_for_enter()
            return

        self.ui.console.print(
            f"[green]✓ {len(bookmarks)} bookmark bulundu![/green]\n"
        )

        if not self.ui.ask_confirmation(f"{len(bookmarks)} bookmark indirilsin mi?"):
            return

        self.ui.console.print("\n[bold cyan]İndirme başlıyor...[/bold cyan]\n")

        successful, failed, skipped, failed_urls = self.twitter_downloader.download_bookmarks(
            progress_callback=self.ui.show_twitter_progress,
        )

        self.ui.show_twitter_summary(successful, failed, failed_urls, skipped)
        self.ui.wait_for_enter()

    def _handle_twitter_single(self):
        """Tek Twitter/X video indirir."""
        url = self.ui.ask_twitter_url()
        if not url:
            return

        self.ui.console.print(
            f"\n[bold green]İndiriliyor...[/bold green] [dim]{url}[/dim]\n"
        )

        try:
            success, message = self.twitter_downloader.download(url)

            if success:
                self.ui.show_success(
                    f"Twitter videosu indirildi!\nKonum: {self.twitter_downloader.twitter_download_path}"
                )
            elif "zaten indirilmiş" in message:
                self.ui.console.print(f"[yellow]○ {message}[/yellow]")
            else:
                self.ui.show_error(f"İndirme hatası: {message}")
        except Exception as e:
            self.ui.show_error(f"İndirme hatası: {str(e)}")

        self.ui.wait_for_enter()

    def _handle_twitter_bulk(self):
        """Toplu Twitter/X video indirir."""
        file_path = self.ui.ask_twitter_bulk_file()
        if not file_path:
            return

        self.ui.print_header(self.config.download_path)

        try:
            urls = self.twitter_downloader.read_urls_from_file(file_path)
            self.ui.console.print(
                f"\n[bold cyan]Toplu İndirme Başlıyor[/bold cyan]\n"
                f"[dim]Dosya: {file_path}[/dim]\n"
                f"[dim]Toplam URL: {len(urls)}[/dim]\n"
            )

            successful, failed, skipped, failed_urls = self.twitter_downloader.bulk_download(
                urls,
                progress_callback=self.ui.show_twitter_progress,
            )

            self.ui.show_twitter_summary(
                successful, failed, failed_urls, skipped)

        except FileNotFoundError as e:
            self.ui.show_error(str(e))
        except ValueError as e:
            self.ui.show_error(str(e))

        self.ui.wait_for_enter()

    def handle_search(self):
        """YouTube'da arama yapar ve sonuçlardan seçilen videoyu indirir."""
        self.ui.push_breadcrumb("YouTube Arama")
        self.ui.print_header(self.config.download_path)

        query = self.ui.ask_search_query()
        if not query:
            return

        self.ui.console.print(
            f"\n[bold cyan]Aranıyor:[/bold cyan] [dim]{query}[/dim]\n"
        )

        try:
            results = self.downloader.search(query)

            if not results:
                self.ui.show_error("Sonuç bulunamadı.")
                self.ui.wait_for_enter()
                self.ui.pop_breadcrumb()
                return

            # Sonuçları göster ve seçim yap
            selected_url = self.ui.ask_search_result(results)

            if selected_url:
                self.perform_download(selected_url)

        except Exception as e:
            self.ui.show_error(f"Arama hatası: {str(e)}")
            self.ui.wait_for_enter()

        self.ui.pop_breadcrumb()

    def perform_download(self, url):
        # Eğer hesap ayarlanmamışsa uyar
        if not self.config.auth_method:
            self.ui.console.print(
                "[yellow]Bilgi: Hesap bağlı değil. Özel playlistler indirilemeyebilir.[/yellow]"
            )

        # Duplicate kontrolü (playlist değilse)
        if "playlist" not in url.lower():
            is_dup, dup_date = self.downloader.history.is_downloaded(
                url, "youtube")
            if is_dup:
                self.ui.show_warning(
                    f"Bu video zaten indirilmiş! ({dup_date})")
                self.ui.wait_for_enter()
                return

        self.ui.console.print(
            f"\n[bold green]İşleniyor...[/bold green] [dim]{url}[/dim]"
        )

        success = False
        error_msg = ""

        # Progress Bar Kurulumu
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=self.ui.console,
        ) as progress:
            task_id = progress.add_task("[cyan]Hazırlanıyor...", total=None)

            def progress_hook(d):
                if d["status"] == "downloading":
                    total_bytes = d.get("total_bytes") or d.get(
                        "total_bytes_estimate")
                    downloaded_bytes = d.get("downloaded_bytes", 0)
                    filename = d.get("filename", "").split("/")[-1]
                    if total_bytes:
                        progress.update(
                            task_id, total=total_bytes, completed=downloaded_bytes
                        )
                    progress.update(
                        task_id,
                        description=f"[green]İndiriliyor:[/green] {filename[:30]}...",
                    )
                elif d["status"] == "finished":
                    progress.update(
                        task_id,
                        description="[bold green]Tamamlandı! İşleniyor...[/bold green]",
                    )

            try:
                self.downloader.download(url, progress_hooks=[progress_hook])
                success = True
            except Exception as e:
                error_msg = str(e)

        # Progress bar kapandıktan sonra sonuçları göster
        if success:
            self.ui.show_success(
                f"İşlem Tamamlandı!\nKonum: {self.config.download_path}"
            )
        else:
            self.ui.show_error(error_msg)

        self.ui.wait_for_enter()

    def handle_settings(self):
        """Ayarlar menüsü."""
        self.ui.push_breadcrumb("Ayarlar")

        while True:
            self.ui.print_header(self.config.download_path)
            choice = self.ui.ask_settings(
                self.config.format_type, self.config.quality)

            if not choice or "Geri Dön" in choice:
                break

            if "Format" in choice:
                fmt = self.ui.ask_format()
                if fmt:
                    self.config.set_format(fmt)
                    self.ui.show_success(f"Format değiştirildi: {fmt}")
            elif "Kalite" in choice:
                ql = self.ui.ask_quality()
                if ql:
                    self.config.set_quality(ql)
                    self.ui.show_success(f"Kalite değiştirildi: {ql}")

        self.ui.pop_breadcrumb()


if __name__ == "__main__":
    app = Application()
    app.run()
