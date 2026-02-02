import sys
import os

# Windows console encoding fix for PyInstaller
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    os.environ['PYTHONIOENCODING'] = 'utf-8'

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
from src.core.youtube import YoutubeDownloader
from src.core.twitter import TwitterDownloader
from src.core.twitter import TwitterDownloader
from src.core.tiktok import TikTokDownloader
from src.core.facebook import FacebookDownloader
from src.core.auth import AuthManager
from src.utils.file_ops import FileManager


class Application:
    def __init__(self):
        self.config = Config()
        self.ui = Interface()
        self.ui.update_theme(self.config.theme_color)
        self.auth_manager = AuthManager(self.config)
        self.downloader = YoutubeDownloader(self.config)
        self.twitter_downloader = TwitterDownloader(self.config)
        self.tiktok_downloader = TikTokDownloader(self.config)
        self.facebook_downloader = FacebookDownloader(self.config)
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
                        ".tiktok.com" in first_lines or
                        "auth_token" in first_lines or
                        "ct0" in first_lines or
                        "sessionid" in first_lines
                    )

                    if is_cookie:
                        # Platform tespiti
                        platform = "Bilinmeyen"
                        if ".twitter.com" in first_lines or ".x.com" in first_lines or "ct0" in first_lines:
                            platform = "Twitter/X"
                        elif ".youtube.com" in first_lines:
                            platform = "YouTube"
                        elif ".tiktok.com" in first_lines:
                            platform = "TikTok"

                        cookie_files.append({
                            "path": str(file),
                            "name": file.name,
                            "size": size,
                            "platform": platform,
                        })
            except (OSError, IOError):
                continue

        return cookie_files

    def _get_tiktok_url_files(self) -> list[dict]:
        """Downloads klasöründeki potansiyel TikTok URL listesi dosyalarını listele."""
        url_files = []

        if not self.downloads_folder.exists():
            return url_files

        # .txt dosyalarını tara
        for file in self.downloads_folder.glob("*.txt"):
            try:
                size = file.stat().st_size
                # URL listesi dosyaları genellikle küçüktür ama birkaç MB olabilir
                if size > 0 and size < 10 * 1024 * 1024:  # 10MB'den küçük
                    # İlk birkaç satırı oku ve TikTok URL içeriyor mu kontrol et
                    with open(file, "r", encoding="utf-8", errors="ignore") as f:
                        first_lines = f.read(2000)

                    # TikTok URL'si var mı kontrol et
                    has_tiktok_urls = (
                        "tiktok.com" in first_lines.lower() and
                        "/video/" in first_lines
                    )

                    # Cookie dosyası DEĞİLse ve TikTok URL içeriyorsa
                    is_cookie = (
                        "# Netscape HTTP Cookie File" in first_lines or
                        "# HTTP Cookie File" in first_lines or
                        "auth_token" in first_lines or
                        "ct0\t" in first_lines or
                        "sessionid\t" in first_lines
                    )

                    if has_tiktok_urls and not is_cookie:
                        # URL sayısını tahmin et
                        url_count = first_lines.count("/video/")
                        if url_count < len(first_lines.split("\n")):
                            # Tam sayıyı hesapla
                            url_count = sum(1 for line in first_lines.split("\n") 
                                          if "tiktok.com" in line.lower() and "/video/" in line)

                        url_files.append({
                            "path": str(file),
                            "name": file.name,
                            "size": size,
                            "url_count": url_count,
                        })
            except (OSError, IOError):
                continue

        # En yeni dosyalar önce gelsin
        url_files.sort(key=lambda x: Path(x["path"]).stat().st_mtime, reverse=True)
        return url_files

    def _select_tiktok_url_file(self) -> str | None:
        """Downloads klasöründen TikTok URL listesi dosyası seç."""
        url_files = self._get_tiktok_url_files()

        choices = ["🔙 İptal"]

        if url_files:
            self.ui.console.print(
                "\n[bold magenta]Downloads klasöründe bulunan TikTok URL dosyaları:[/bold magenta]"
            )

            for uf in url_files:
                size_kb = uf["size"] / 1024
                url_count = uf.get("url_count", "?")
                label = f"📄 {uf['name']} (~{url_count} video, {size_kb:.1f} KB)"
                choices.append(label)
        else:
            self.ui.console.print(
                "[dim]Downloads klasöründe TikTok URL dosyası bulunamadı.[/dim]"
            )

        choices.append("📝 Manuel Dosya Yolu Gir")

        selected = questionary.select(
            "TikTok URL listesi seçin:",
            choices=choices,
            style=self.ui.custom_style,
        ).ask()

        if not selected or "İptal" in selected:
            return None

        if "Manuel" in selected:
            path = questionary.text(
                "URL listesi dosya yolu (.txt):",
                style=self.ui.custom_style,
            ).ask()
            return path.strip().strip('"').strip("'") if path else None

        # Seçilen dosyayı bul
        for uf in url_files:
            if uf["name"] in selected:
                return uf["path"]

        return None

    def _get_tiktok_export_files(self) -> list[dict]:
        """Downloads klasöründeki potansiyel TikTok veri export dosyalarını listele."""
        export_files = []

        if not self.downloads_folder.exists():
            return export_files

        # ZIP ve JSON dosyalarını tara
        for pattern in ["*.zip", "*.json"]:
            for file in self.downloads_folder.glob(pattern):
                try:
                    size = file.stat().st_size
                    # TikTok export dosyaları genellikle birkaç MB
                    if size > 1024 and size < 500 * 1024 * 1024:  # 1KB - 500MB
                        # Dosya adında TikTok ile ilgili bir şey var mı?
                        name_lower = file.name.lower()
                        is_likely_tiktok = (
                            "tiktok" in name_lower or
                            "user_data" in name_lower or
                            "data_export" in name_lower or
                            "export" in name_lower
                        )

                        # ZIP dosyası için içeriği kontrol et
                        if file.suffix.lower() == ".zip":
                            import zipfile
                            try:
                                with zipfile.ZipFile(file, 'r') as zf:
                                    file_list = zf.namelist()
                                    # TikTok export yapısı var mı?
                                    is_likely_tiktok = is_likely_tiktok or any(
                                        "like" in f.lower() or 
                                        "favorite" in f.lower() or
                                        "activity" in f.lower()
                                        for f in file_list[:20]  # İlk 20 dosyaya bak
                                    )
                            except (zipfile.BadZipFile, OSError):
                                continue

                        # JSON dosyası için içeriği kontrol et
                        elif file.suffix.lower() == ".json":
                            try:
                                with open(file, "r", encoding="utf-8", errors="ignore") as f:
                                    first_content = f.read(5000)
                                    is_likely_tiktok = is_likely_tiktok or (
                                        ("tiktok" in first_content.lower()) or
                                        ("Like List" in first_content) or
                                        ("Favorite" in first_content) or
                                        ("Activity" in first_content)
                                    )
                            except (OSError, IOError):
                                continue

                        if is_likely_tiktok:
                            size_mb = size / (1024 * 1024)
                            export_files.append({
                                "path": str(file),
                                "name": file.name,
                                "size": size,
                                "size_display": f"{size_mb:.1f} MB" if size_mb >= 1 else f"{size/1024:.1f} KB",
                                "type": file.suffix.upper()[1:],  # ZIP or JSON
                            })
                except (OSError, IOError):
                    continue

        # En yeni dosyalar önce gelsin
        export_files.sort(key=lambda x: Path(x["path"]).stat().st_mtime, reverse=True)
        return export_files

    def _select_tiktok_export_file(self) -> str | None:
        """Downloads klasöründen TikTok veri export dosyası seç."""
        export_files = self._get_tiktok_export_files()

        self.ui.console.print(
            "\n[bold magenta]TikTok Veri Export İndirme[/bold magenta]\n"
        )
        self.ui.console.print(
            "[bold cyan]TikTok'tan veri export nasıl alınır:[/bold cyan]"
            "\n1. TikTok uygulamasını açın"
            "\n2. Profil > Menü (☰) > Ayarlar ve gizlilik"
            "\n3. Hesap > Verilerinizi indirin"
            "\n4. 'JSON' formatını seçin ve 'Veri Talep Et' deyin"
            "\n5. Birkaç gün içinde bildirim alacaksınız"
            "\n6. İndirilen ZIP veya JSON dosyasını aşağıdan seçin"
            "\n"
        )

        choices = ["🔙 İptal"]

        if export_files:
            self.ui.console.print(
                "[bold]Downloads klasöründe bulunan potansiyel TikTok export dosyaları:[/bold]"
            )

            for ef in export_files:
                label = f"📦 {ef['name']} ({ef['type']}, {ef['size_display']})"
                choices.append(label)

        choices.append("📝 Manuel Dosya Yolu Gir")

        selected = questionary.select(
            "TikTok veri export dosyası seçin:",
            choices=choices,
            style=self.ui.custom_style,
        ).ask()

        if not selected or "İptal" in selected:
            return None

        if "Manuel" in selected:
            path = questionary.text(
                "Veri export dosya yolu (ZIP veya JSON):",
                style=self.ui.custom_style,
            ).ask()
            return path.strip().strip('"').strip("'") if path else None

        # Seçilen dosyayı bul
        for ef in export_files:
            if ef["name"] in selected:
                return ef["path"]

        return None

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
                style=self.ui.custom_style,
            ).ask()

            if manual:
                path = questionary.text(
                    "Cookie dosya yolu:",
                    style=self.ui.custom_style,
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
            style=self.ui.custom_style,
        ).ask()

        if not selected or "İptal" in selected:
            return None

        if "Manuel Giriş" in selected:
            path = questionary.text(
                "Cookie dosya yolu:",
                style=self.ui.custom_style,
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

        # TikTok durumu
        if self.config.tiktok_cookies_file:
            tt_name = self.config.tiktok_username or "Bağlı"
            status_parts.append(f"[magenta]TikTok[/magenta]: @{tt_name}")

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

                if "YouTube" in choice:
                    self.handle_youtube_menu()
                elif "TikTok" in choice:
                    self.handle_tiktok_download()
                elif "Twitter/X" in choice:
                    self.handle_twitter_download()
                elif "Facebook" in choice:
                    self.handle_facebook_download()
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
            "[bold cyan]Gorusmek uzere![/bold cyan]",
            justify="center",
        )

    def handle_youtube_menu(self):
        """YouTube işlemlerini yönet."""
        self.ui.push_breadcrumb("YouTube")
        
        while True:
            self.ui.print_header(self.config.download_path)
            
            # YouTube Hesap Durumu (Opsiyonel: misafir mi bağlı mı gösterilebilir)
            if self.config.auth_method:
                yt_name = self.config.channel_name or "Bağlı"
                self.ui.console.print(
                    f"[green]● YouTube[/green]: {yt_name}",
                    justify="center",
                )
            
            choice = self.ui.ask_youtube_menu()
            
            if not choice or "Geri Dön" in choice:
                break
            
            if "Link ile İndir" in choice:
                self.handle_download()
            elif "YouTube'da Ara" in choice:
                self.handle_search()
            elif "Kütüphanemden İndir" in choice:
                self.handle_library_download()
            elif "İndirilenleri Yönet" in choice:
                self.handle_downloads_manager()
        
        self.ui.pop_breadcrumb()

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
        tt_connected = bool(self.config.tiktok_cookies_file)

        if yt_connected or tw_connected or tt_connected:
            self.ui.console.print("\n[bold]Mevcut Bağlantılar:[/bold]")
            if yt_connected:
                yt_name = self.config.channel_name or "Bağlı"
                self.ui.console.print(
                    f"  [green]●[/green] [red]YouTube[/red]: {yt_name}")
            if tw_connected:
                tw_name = self.config.twitter_username or "Bağlı"
                self.ui.console.print(
                    f"  [green]●[/green] [cyan]Twitter[/cyan]: @{tw_name}")
            if tt_connected:
                tt_name = self.config.tiktok_username or "Bağlı"
                self.ui.console.print(
                    f"  [green]●[/green] [magenta]TikTok[/magenta]: @{tt_name}")
            self.ui.console.print("")

        # Yöntem Seçimi
        auth_choice = self.ui.ask_auth_method(yt_connected, tw_connected, tt_connected)

        if not auth_choice or "Geri Dön" in auth_choice:
            self.ui.pop_breadcrumb()
            return

        if "Tek Dosya ile Toplu Giriş" in auth_choice:
            self._handle_unified_login()

        elif "YouTube Cookie ile Bağlan" in auth_choice:
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

        elif "TikTok Cookie ile Bağlan" in auth_choice:
            self._handle_tiktok_cookie_login()

        elif "YouTube Oturumunu Kapat" in auth_choice:
            self.auth_manager.logout()
            self.ui.show_success("YouTube oturumu kapatıldı.")
            self.ui.wait_for_enter()

        elif "Twitter Oturumunu Kapat" in auth_choice:
            self.config.twitter_cookies_file = None
            self.config.twitter_username = None
            self.ui.show_success("Twitter oturumu kapatıldı.")
            self.ui.wait_for_enter()

        elif "TikTok Oturumunu Kapat" in auth_choice:
            self.config.tiktok_cookies_file = None
            self.config.tiktok_username = None
            self.ui.show_success("TikTok oturumu kapatıldı.")
            self.ui.wait_for_enter()

        elif "Tüm Oturumları Kapat" in auth_choice:
            self.auth_manager.logout()
            self.config.twitter_cookies_file = None
            self.config.twitter_username = None
            self.config.tiktok_cookies_file = None
            self.config.tiktok_username = None
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

    # ==================== TikTok Methods ====================

    def _handle_tiktok_cookie_login(self):
        """TikTok için cookie dosyası ile giriş."""
        self.ui.console.print(
            "\n[bold magenta]TikTok Cookie Girişi[/bold magenta]")
        self.ui.console.print(
            "[dim]tiktok.com'dan export edilmiş cookie dosyası gerekli[/dim]")
        self.ui.console.print(
            "[dim]Cookie'de 'sessionid' veya 'sessionid_ss' olmalı[/dim]\n")

        cookies_file = self._select_cookie_file("TikTok")
        if not cookies_file:
            return

        self.ui.console.print("[yellow]TikTok kontrol ediliyor...[/yellow]")

        success, error_msg = self.tiktok_downloader.validate_tiktok_cookies(
            cookies_file)
        if success:
            self.ui.show_success("TikTok bağlandı!")
        else:
            self.ui.show_error(
                f"TikTok'a bağlanılamadı.\n"
                f"Hata: {error_msg}\n\n"
                f"Cookie dosyasının tiktok.com'dan alındığından emin olun."
            )

        self.ui.wait_for_enter()

    def handle_tiktok_download(self):
        """TikTok video indirme işlemlerini yönetir."""
        self.ui.push_breadcrumb("TikTok")

        while True:
            self.ui.print_header(self.config.download_path)

            # TikTok oturum durumunu göster
            if self.config.tiktok_cookies_file:
                tt_name = self.config.tiktok_username or "Bağlı"
                self.ui.console.print(
                    f"[green]● TikTok[/green]: @{tt_name}",
                    justify="center",
                )
            else:
                self.ui.console.print(
                    "[dim]● TikTok Bağlı Değil (Liked/Bookmarks için Hesap İşlemlerinden bağlanın)[/dim]",
                    justify="center",
                )

            has_cookies = bool(self.config.tiktok_cookies_file)
            choice = self.ui.ask_tiktok_menu(has_cookies)

            if not choice or "Geri Dön" in choice:
                break

            if "Veri Export" in choice:
                self._handle_tiktok_data_export()
            elif "Liked" in choice:
                self._handle_tiktok_liked()
            elif "Bookmarks" in choice:
                self._handle_tiktok_bookmarks()
            elif "Tek Link" in choice:
                self._handle_tiktok_single()
            elif "Toplu İndir" in choice:
                self._handle_tiktok_bulk()
            elif "URL Çıkarma" in choice:
                self._handle_tiktok_show_script()

        self.ui.pop_breadcrumb()

    def _handle_tiktok_liked(self):
        """TikTok liked videolarını indirir (URL listesinden)."""
        self.ui.console.print(
            "\n[bold magenta]Liked Videolar İndirme[/bold magenta]\n"
        )
        self.ui.console.print(
            "[dim]TikTok API'sı liked videolara doğrudan erişime izin vermez.[/dim]"
        )
        self.ui.console.print(
            "[dim]Tampermonkey scripti veya tarayıcı konsolu ile URL listesi oluşturun.[/dim]\n"
        )

        file_path = self._select_tiktok_url_file()
        if not file_path:
            return

        self._download_tiktok_from_file(file_path, "Liked Videolar")

    def _handle_tiktok_bookmarks(self):
        """TikTok bookmarks/favorites videolarını indirir (URL listesinden)."""
        self.ui.console.print(
            "\n[bold magenta]Bookmarks İndirme[/bold magenta]\n"
        )
        self.ui.console.print(
            "[dim]TikTok API'sı bookmarks'lara doğrudan erişime izin vermez.[/dim]"
        )
        self.ui.console.print(
            "[dim]Tampermonkey scripti veya tarayıcı konsolu ile URL listesi oluşturun.[/dim]\n"
        )

        file_path = self._select_tiktok_url_file()
        if not file_path:
            return

        self._download_tiktok_from_file(file_path, "Bookmarks")

    def _download_tiktok_from_file(self, file_path: str, source_name: str):
        """TikTok URL dosyasından indirme yapar."""
        self.ui.print_header(self.config.download_path)

        try:
            urls = self.tiktok_downloader.read_urls_from_file(file_path)
            self.ui.console.print(
                f"\n[bold magenta]{source_name} İndirme Başlıyor[/bold magenta]\n"
                f"[dim]Dosya: {file_path}[/dim]\n"
                f"[dim]Toplam URL: {len(urls)}[/dim]\n"
            )

            if not self.ui.ask_confirmation(f"{len(urls)} video indirilsin mi?"):
                return

            self.ui.console.print("\n[bold magenta]İndirme başlıyor...[/bold magenta]\n")

            successful, failed, skipped, failed_urls = self.tiktok_downloader.bulk_download(
                urls,
                progress_callback=self.ui.show_tiktok_progress,
            )

            self.ui.show_tiktok_summary(successful, failed, failed_urls, skipped)

        except FileNotFoundError as e:
            self.ui.show_error(str(e))
        except ValueError as e:
            self.ui.show_error(str(e))

        self.ui.wait_for_enter()

    def _handle_tiktok_single(self):
        """Tek TikTok video indirir."""
        url = self.ui.ask_tiktok_url()
        if not url:
            return

        self.ui.console.print(
            f"\n[bold green]İndiriliyor...[/bold green] [dim]{url}[/dim]\n"
        )

        try:
            success, message = self.tiktok_downloader.download(url)

            if success:
                self.ui.show_success(
                    f"TikTok videosu indirildi!\nKonum: {self.tiktok_downloader.tiktok_download_path}"
                )
            elif "zaten indirilmiş" in message:
                self.ui.console.print(f"[yellow]○ {message}[/yellow]")
            else:
                self.ui.show_error(f"İndirme hatası: {message}")
        except Exception as e:
            self.ui.show_error(f"İndirme hatası: {str(e)}")

        self.ui.wait_for_enter()

    def _handle_tiktok_bulk(self):
        """Toplu TikTok video indirir."""
        file_path = self._select_tiktok_url_file()
        if not file_path:
            return

        self._download_tiktok_from_file(file_path, "Toplu İndirme")

    def _handle_tiktok_show_script(self):
        """TikTok URL çıkarma scriptini gösterir."""
        self.ui.clear_screen()
        script = self.tiktok_downloader.get_url_extraction_script()
        self.ui.show_url_extraction_script(script)
        self.ui.wait_for_enter()

    def _handle_tiktok_data_export(self):
        """TikTok veri export dosyasından (JSON/ZIP) videoları indirir."""
        file_path = self._select_tiktok_export_file()
        if not file_path:
            return
        
        file_path = file_path.strip().strip('"').strip("'")
        
        self.ui.print_header(self.config.download_path)
        self.ui.console.print("[yellow]TikTok veri export dosyası analiz ediliyor...[/yellow]\n")
        
        try:
            # Parse the data export
            data = self.tiktok_downloader.parse_tiktok_data_export(file_path)
            
            liked_count = len(data.get("liked", []))
            favorites_count = len(data.get("favorites", []))
            watched_count = len(data.get("watched", []))
            
            if liked_count == 0 and favorites_count == 0 and watched_count == 0:
                self.ui.show_error(
                    "Veri export dosyasında video bulunamadı!\n"
                    "Dosyanın TikTok'tan alınmış geçerli bir export olduğundan emin olun."
                )
                self.ui.wait_for_enter()
                return
            
            # Show summary
            self.ui.show_tiktok_data_export_info(liked_count, favorites_count, watched_count)
            
            # Ask which category to download
            category_choice = self.ui.ask_tiktok_data_export_category(
                liked_count, favorites_count, watched_count
            )
            
            if not category_choice or "Geri" in category_choice:
                return
            
            # Determine category and get URLs
            if "Liked" in category_choice:
                urls = data["liked"]
                category_name = "Liked Videolar"
            elif "Favorites" in category_choice or "Bookmarks" in category_choice:
                urls = data["favorites"]
                category_name = "Favorites/Bookmarks"
            elif "İzleme" in category_choice:
                urls = data["watched"]
                category_name = "İzleme Geçmişi"
            else:
                return
            
            if not urls:
                self.ui.show_error("Bu kategoride video bulunamadı!")
                self.ui.wait_for_enter()
                return
            
            # Confirm download
            self.ui.console.print(
                f"\n[bold magenta]{category_name}[/bold magenta]: {len(urls)} video bulundu\n"
            )
            
            if not self.ui.ask_confirmation(f"{len(urls)} video indirilsin mi?"):
                return
            
            # Download
            self.ui.console.print("\n[bold magenta]İndirme başlıyor...[/bold magenta]\n")
            
            successful, failed, skipped, failed_urls = self.tiktok_downloader.bulk_download(
                urls,
                progress_callback=self.ui.show_tiktok_progress,
            )
            
            self.ui.show_tiktok_summary(successful, failed, failed_urls, skipped)
            
        except FileNotFoundError as e:
            self.ui.show_error(str(e))
        except ValueError as e:
            self.ui.show_error(str(e))
        except Exception as e:
            self.ui.show_error(f"Dosya işlenirken hata oluştu: {str(e)}")
        
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

            if "Tema" in choice:
                color_choice = self.ui.ask_theme_color()
                if color_choice and "Geri" not in color_choice:
                    # Renk adını ayıkla
                    theme_map = {
                        "Ubuntu": "ubuntu",
                        "Macintosh": "macintosh",
                        "Fedora": "fedora"
                    }
                    selected_theme = "ubuntu"
                    for key, val in theme_map.items():
                        if key in color_choice:
                            selected_theme = val
                            break
                    
                    self.config.theme_color = selected_theme
                    self.ui.update_theme(selected_theme)
                    self.ui.show_success(f"Tema değiştirildi: {selected_theme.title()}")

            elif "Format" in choice:
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

    def _handle_unified_login(self):
        """Tek cookie dosyası ile toplu giriş."""
        self.ui.console.print("\n[bold cyan]Universal Cookie Girişi[/bold cyan]")
        self.ui.console.print(
            "[dim]YouTube ve/veya Twitter/TikTok içeren cookie dosyasını seçin[/dim]\n"
        )
        
        cookies_file = self._select_cookie_file("Universal")
        if not cookies_file:
            return
            
        self.ui.console.print("[yellow]Cookie dosyası analiz ediliyor...[/yellow]")
        
        results = []
        
        # 1. YouTube Kontrolü
        if self.auth_manager.validate_cookies_file(cookies_file):
            self.config.cookies_file = cookies_file
            self.config.auth_method = "cookies_file"
            yt_name = self.config.channel_name or "Bağlı"
            results.append(f"[green]✓ YouTube:[/green] {yt_name}")
        else:
            results.append("[red]✗ YouTube:[/red] Başarısız")
            
        # 2. Twitter Kontrolü
        success, msg = self.twitter_downloader.validate_twitter_cookies(cookies_file)
        if success:
            self.config.twitter_cookies_file = cookies_file
            results.append(f"[green]✓ Twitter:[/green] Bağlandı")
        else:
            results.append(f"[red]✗ Twitter:[/red] Başarısız ({msg})")
            
        # 3. TikTok Kontrolü
        try:
            with open(cookies_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if '.tiktok.com' in content:
                     self.config.tiktok_cookies_file = cookies_file
                     results.append("[yellow]○ TikTok:[/yellow] Cookie bulundu")
                else:
                     results.append("[dim]○ TikTok:[/dim] Cookie bulunamadı")
        except:
             results.append("[red]✗ TikTok:[/red] Dosya okuma hatası")

        # 4. Facebook Kontrolü
        fb_success, fb_msg = self.facebook_downloader.validate_facebook_cookies(cookies_file)
        if fb_success:
             self.config.facebook_cookies_file = cookies_file
             results.append("[green]✓ Facebook:[/green] Bağlandı")
        else:
             results.append(f"[red]✗ Facebook:[/red] {fb_msg}")

        # Sonuçları göster
        self.ui.console.print("\n[bold]Giriş Sonuçları:[/bold]")
        for res in results:
            self.ui.console.print(f"  {res}")
            
        self.ui.wait_for_enter()

    def handle_facebook_download(self):
        """Facebook işlemlerini yönet."""
        self.ui.push_breadcrumb("Facebook")
        while True:
            self.ui.print_header(self.config.download_path)
            
            choice = self.ui.ask_facebook_menu()
            
            if not choice or "Geri Dön" in choice:
                break
            
            if "Tek Link" in choice:
                self._handle_facebook_single()
            elif "Toplu İndir" in choice:
                self._handle_facebook_bulk()
            elif "Saved URL Extractor" in choice:
                # Script dosyasının yolunu göster
                script_path = Path("scripts/facebook_saved_extractor.user.js").absolute()
                self.ui.console.print(
                    f"\n[bold green]Facebook Saved Extractor Script:[/bold green]\n"
                    f"[white]{script_path}[/white]\n\n"
                    "[dim]Bu dosyayı Tampermonkey'e ekleyerek Facebook 'Saved' sayfasından linkleri toplayabilirsiniz.[/dim]"
                )
                self.ui.wait_for_enter()
                
        self.ui.pop_breadcrumb()

    def _handle_facebook_single(self):
        url = self.ui.ask_facebook_url()
        if not url: return
        self.ui.console.print("[yellow]İndiriliyor...[/yellow]")
        success, msg = self.facebook_downloader.download(url)
        if success: self.ui.show_success(msg)
        else: self.ui.show_error(msg)
        self.ui.wait_for_enter()

    def _handle_facebook_bulk(self):
        file_path = self.ui.ask_facebook_bulk_file()
        if not file_path: return
        
        self.ui.print_header(self.config.download_path)
        self.ui.console.print(f"\n[bold cyan]Toplu İndirme Başlıyor[/bold cyan]\n[dim]Dosya: {file_path}[/dim]\n")
        
        successful, failed, failed_urls, skipped = self.facebook_downloader.download_bulk(
            file_path, progress_callback=self.ui.show_facebook_progress
        )
        # Özet göster (Twitter özetini kullanabiliriz veya generic bir özet yazabiliriz)
        # Şimdilik basit özet
        self.ui.console.print(f"\n[bold green]Tamamlandı![/bold green] Başarılı: {successful}, Hatalı: {failed}")
        if failed_urls:
             self.ui.show_error(f"{len(failed_urls)} video indirilemedi.")
        self.ui.wait_for_enter()


if __name__ == "__main__":
    app = Application()
    app.run()
