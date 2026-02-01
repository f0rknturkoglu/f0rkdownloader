import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import questionary
from src.ui.theme import custom_style, COLORS, APP_TITLE

console = Console()


# Sabit UI sembolleri
class Icons:
    BACK = "◀"
    FORWARD = "▶"
    SUCCESS = "✓"
    ERROR = "✗"
    SKIP = "○"
    DOWNLOAD = "⬇"
    SEARCH = "🔍"
    FOLDER = "📂"
    FILE = "📄"
    SETTINGS = "⚙"
    ACCOUNT = "👤"
    EXIT = "🚪"
    YOUTUBE = "🔴"
    TWITTER = "🐦"
    CONNECTED = "●"
    DISCONNECTED = "○"


class Interface:
    def __init__(self):
        self.console = console
        self.breadcrumb: list[str] = []

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def push_breadcrumb(self, name: str):
        """Breadcrumb'a yeni konum ekle."""
        self.breadcrumb.append(name)

    def pop_breadcrumb(self):
        """Breadcrumb'dan son konumu çıkar."""
        if self.breadcrumb:
            self.breadcrumb.pop()

    def clear_breadcrumb(self):
        """Breadcrumb'u temizle."""
        self.breadcrumb.clear()

    def _get_breadcrumb_text(self) -> str:
        """Breadcrumb metnini döndür."""
        if not self.breadcrumb:
            return ""
        return " › ".join(self.breadcrumb)

    def print_header(self, download_path: str):
        self.clear_screen()
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_row(
            f"[bold {COLORS['primary']}]{APP_TITLE}[/bold {COLORS['primary']}]"
        )
        grid.add_row(
            f"[bold {COLORS['text']}]f0rkn_d0wnl0ader - Premium & Playlist Tool[/bold {COLORS['text']}]"
        )

        # Breadcrumb göster
        if self.breadcrumb:
            breadcrumb_text = self._get_breadcrumb_text()
            grid.add_row(f"[cyan]{breadcrumb_text}[/cyan]")

        grid.add_row(f"[dim]İndirme Konumu: {download_path}[/dim]")

        self.console.print(
            Panel(grid, style=COLORS["primary"],
                  border_style=COLORS["primary"])
        )

    def show_success(self, message: str):
        self.console.print(
            Panel(
                f"[bold {COLORS['success']}]{Icons.SUCCESS} {message}[/bold {COLORS['success']}]",
                border_style=COLORS["success"],
            )
        )

    def show_error(self, message: str):
        self.console.print(
            Panel(
                f"[bold {COLORS['error']}]{Icons.ERROR} Hata:[/bold {COLORS['error']}]\n{message}",
                border_style=COLORS["error"],
            )
        )

    def show_warning(self, message: str):
        """Uyarı mesajı göster."""
        self.console.print(f"[yellow]{Icons.SKIP} {message}[/yellow]")

    def show_info(self, message: str):
        """Bilgi mesajı göster."""
        self.console.print(f"[cyan]ℹ {message}[/cyan]")

    def wait_for_enter(self, message: str = "Devam etmek için Enter..."):
        """Enter bekle."""
        self.console.print(f"\n[dim]{message}[/dim]")
        input()

    def ask_main_menu(self, stats: dict | None = None):
        """Ana menü - istatistiklerle birlikte."""
        choices = [
            f"{Icons.DOWNLOAD}  Link ile İndir (Video/Playlist)",
            f"{Icons.SEARCH}  YouTube'da Ara",
            f"{Icons.FOLDER}  Kütüphanemden İndir (Özel Playlistler)",
            f"{Icons.TWITTER}  Twitter/X Video İndir",
        ]

        # İndirilenler seçeneği - istatistikle
        if stats and stats.get("total", 0) > 0:
            total = stats["total"]
            choices.append(f"📂  İndirilenleri Yönet ({total} dosya)")
        else:
            choices.append("📂  İndirilenleri Yönet")

        choices.extend([
            f"{Icons.ACCOUNT}  Hesap İşlemleri",
            f"{Icons.SETTINGS}  Ayarlar",
            f"{Icons.EXIT} Çıkış",
        ])

        return questionary.select(
            "Ne yapmak istersiniz?",
            choices=choices,
            style=custom_style,
            instruction="(↑↓ ile seç, Enter ile onayla)",
        ).ask()

    def show_file_tree(self, tree):
        self.clear_screen()
        self.console.print(
            Panel(
                tree,
                title="[bold orange1]İndirilen Dosyalar[/bold orange1]",
                subtitle=f"[dim]{Icons.BACK} Geri dönmek için seçin[/dim]",
                border_style="orange1",
            )
        )

    def ask_file_to_open(self, file_list):
        """Dosya seçimi - klasör filtreleme ve arama desteği ile."""
        while True:
            # Klasörleri çıkar
            folders = set()
            for f in file_list:
                parts = f.split("\\") if "\\" in f else f.split("/")
                if len(parts) > 1:
                    folders.add(parts[0])

            # Ana menü seçenekleri
            menu_choices = [f"{Icons.BACK} Geri Dön"]

            if folders:
                menu_choices.append(f"{Icons.FOLDER} Klasöre Göre Filtrele")

            menu_choices.append(f"{Icons.SEARCH} Dosya Ara")
            menu_choices.append(f"{Icons.FILE} Tüm Dosyaları Listele")

            action = questionary.select(
                f"İndirilenler ({len(file_list)} dosya):",
                choices=menu_choices,
                style=custom_style,
                instruction="(↑↓ ile seç, Enter ile onayla)",
            ).ask()

            if not action or "Geri Dön" in action:
                return "Geri Dön"

            if "Klasöre Göre" in action:
                # Klasör seçimi
                folder_choices = [f"{Icons.BACK} Geri"] + sorted(list(folders))
                selected_folder = questionary.select(
                    "Klasör seçin:",
                    choices=folder_choices,
                    style=custom_style,
                ).ask()

                if not selected_folder or "Geri" in selected_folder:
                    continue

                # Seçilen klasördeki dosyaları filtrele
                filtered = [
                    f for f in file_list if f.startswith(selected_folder)]
                return self._paginated_file_select(filtered, f"📂 {selected_folder}")

            elif "Dosya Ara" in action:
                query = questionary.text(
                    "Arama (dosya adı):",
                    style=custom_style,
                ).ask()

                if not query:
                    continue

                # Arama sonuçları
                filtered = [f for f in file_list if query.lower() in f.lower()]
                if not filtered:
                    self.console.print("[yellow]Sonuç bulunamadı.[/yellow]")
                    continue

                return self._paginated_file_select(filtered, f"🔍 '{query}'")

            elif "Tüm Dosyaları" in action:
                return self._paginated_file_select(file_list, "Tüm Dosyalar")

    def _paginated_file_select(self, file_list, title="Dosyalar", page_size=30):
        """Sayfalı dosya seçimi."""
        if not file_list:
            return "Geri Dön"

        total_pages = (len(file_list) - 1) // page_size + 1
        current_page = 0

        while True:
            start_idx = current_page * page_size
            end_idx = min(start_idx + page_size, len(file_list))
            page_files = file_list[start_idx:end_idx]

            choices = [f"{Icons.BACK} Geri Dön"]

            # Sayfa navigasyonu
            if total_pages > 1:
                if current_page > 0:
                    choices.append("⬅ Önceki Sayfa")
                if current_page < total_pages - 1:
                    choices.append("➡ Sonraki Sayfa")

            choices.extend(page_files)

            page_info = f" (Sayfa {current_page + 1}/{total_pages})" if total_pages > 1 else ""
            result = questionary.select(
                f"{title}{page_info} - {len(file_list)} dosya:",
                choices=choices,
                style=custom_style,
                instruction="(↑↓ ile seç, Enter ile onayla)",
            ).ask()

            if not result or "Geri Dön" in result:
                return "Geri Dön"
            elif "Önceki Sayfa" in result:
                current_page -= 1
            elif "Sonraki Sayfa" in result:
                current_page += 1
            else:
                return result

    def ask_file_action(self, filename):
        return questionary.select(
            f"{filename} ile ne yapmak istersiniz?",
            choices=[
                f"{Icons.FORWARD}  Aç/Oynat",
                "🗑  Sil",
                f"{Icons.BACK} İptal",
            ],
            style=custom_style,
        ).ask()

    def ask_confirmation(self, message):
        return questionary.confirm(
            message,
            default=False,
            style=custom_style,
            instruction="(y/n)",
        ).ask()

    def ask_auth_method(self, yt_connected: bool = False, tw_connected: bool = False):
        choices = []

        # YouTube bağlantı seçenekleri
        if not yt_connected:
            choices.append(f"{Icons.YOUTUBE} YouTube Cookie ile Bağlan")
            choices.append("🍪 YouTube Tarayıcı Çerezleri")
        else:
            choices.append(f"{Icons.YOUTUBE} YouTube Oturumunu Kapat")

        # Twitter bağlantı seçenekleri
        if not tw_connected:
            choices.append(f"{Icons.TWITTER} Twitter/X Cookie ile Bağlan")
        else:
            choices.append(f"{Icons.TWITTER} Twitter Oturumunu Kapat")

        # Tümünü kapat
        if yt_connected and tw_connected:
            choices.append(f"{Icons.EXIT} Tüm Oturumları Kapat")

        choices.append(f"{Icons.BACK} Geri Dön")

        return questionary.select(
            "Hesap İşlemleri:",
            choices=choices,
            style=custom_style,
            instruction="(↑↓ ile seç, Enter ile onayla)",
        ).ask()

    def ask_cookies_file(self):
        """Cookie dosyası yolunu sor."""
        self.console.print(
            "\n[bold cyan]Cookie Dosyası Nasıl Elde Edilir:[/bold cyan]"
        )
        self.console.print(
            "[dim]1. Chrome/Edge'e 'Get cookies.txt LOCALLY' eklentisini kurun[/dim]"
        )
        self.console.print(
            "[dim]2. Giriş yapmak istediğiniz siteye gidin (youtube.com veya x.com)[/dim]"
        )
        self.console.print(
            "[dim]3. Eklenti ikonuna tıklayın ve 'Export' deyin[/dim]"
        )
        self.console.print(
            "[dim]4. Dosyayı kaydedin ve buraya sürükle-bırak yapın[/dim]\n"
        )
        self.console.print(
            "[yellow]NOT: Cookie dosyası otomatik olarak hem YouTube hem Twitter için denenecek.[/yellow]\n"
        )

        return questionary.text(
            "Cookie dosyası yolunu girin (sürükle-bırak):",
            style=custom_style,
        ).ask()

    def ask_playlist_selection(self, playlists):
        choices = []
        for pl in playlists:
            title = pl.get("title", "Bilinmeyen Playlist")
            url = pl.get("url", "")
            if title and url:
                choices.append(f"{Icons.FOLDER} {title} | {url}")

        choices.append(f"{Icons.BACK} Geri Dön")

        return questionary.select(
            "İndirmek istediğiniz playlisti seçin:",
            choices=choices,
            style=custom_style,
            instruction="(↑↓ ile seç, Enter ile onayla)",
        ).ask()

    def ask_url(self):
        return questionary.text(
            "Link Yapıştırın (Video veya Playlist):", style=custom_style
        ).ask()

    def ask_browser(self):
        choices = [
            "Chrome (Arc için bunu deneyin)",
            "Edge",
            "Safari",
            "Firefox",
            "Opera",
            "Brave",
            "Tarayıcı Kullanma (Halka açık videolar için)",
        ]
        selection = questionary.select(
            "Hangi tarayıcıdan oturum bilgisi (cookies) çekilsin?",
            choices=choices,
            style=custom_style,
        ).ask()

        if "Chrome" in selection:
            return "chrome"
        if "Edge" in selection:
            return "edge"
        if "Safari" in selection:
            return "safari"
        if "Firefox" in selection:
            return "firefox"
        if "Opera" in selection:
            return "opera"
        if "Brave" in selection:
            return "brave"
        return None

    def ask_settings(self, current_format, current_quality):
        return questionary.select(
            "Ayarlar",
            choices=[
                f"🎬 Format Değiştir (Şu an: {current_format})",
                f"📊 Kalite Ayarı (Şu an: {current_quality})",
                f"{Icons.BACK} Geri Dön",
            ],
            style=custom_style,
            instruction="(↑↓ ile seç, Enter ile onayla)",
        ).ask()

    def ask_format(self):
        return questionary.select(
            "Format Seçin:", choices=["Video", "Sadece Ses (MP3)"], style=custom_style
        ).ask()

    def ask_quality(self):
        return questionary.select(
            "Video Kalitesi Seçin:",
            choices=[
                "En İyi (bestvideo+bestaudio)",
                "1080p (Video)",
                "720p (Video)",
                "En Düşük (Veri Tasarrufu)",
            ],
            style=custom_style,
        ).ask()

    def ask_search_query(self):
        return questionary.text("Arama yapın:", style=custom_style).ask()

    def format_duration(self, seconds):
        """Saniyeyi dakika:saniye formatına çevirir."""
        if not seconds:
            return "??:??"
        minutes, secs = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    def format_views(self, count):
        """Görüntülenme sayısını formatlar."""
        if not count:
            return "? görüntülenme"
        if count >= 1_000_000:
            return f"{count / 1_000_000:.1f}M görüntülenme"
        if count >= 1_000:
            return f"{count / 1_000:.1f}K görüntülenme"
        return f"{count} görüntülenme"

    def ask_search_result(self, results):
        """İndirmek istediğiniz videoyu seçin."""
        choices = []
        for video in results:
            duration = self.format_duration(video.get("duration"))
            channel = video.get("channel", "Bilinmeyen")[:20]
            title = video.get("title", "Bilinmeyen")[:50]
            views = self.format_views(video.get("view_count"))

            choice_text = f"{Icons.FORWARD} {title} [{duration}] - {channel} ({views})"
            choices.append({"name": choice_text, "value": video.get("url")})

        choices.append({"name": f"{Icons.BACK} Geri Dön", "value": None})

        return questionary.select(
            "İndirmek istediğiniz videoyu seçin:",
            choices=choices,
            style=custom_style,
            instruction="(↑↓ ile seç, Enter ile onayla)",
        ).ask()

    # ==================== Twitter/X Methods ====================

    def ask_twitter_menu(self, has_cookies: bool = False):
        """Twitter/X indirme menüsü."""
        choices = []

        if has_cookies:
            choices.append("🔖  Bookmarks'larımı İndir")

        choices.extend([
            "🔗  Tek Link ile İndir",
            "📋  Toplu İndir (Dosyadan)",
            f"{Icons.BACK}  Geri Dön",
        ])

        return questionary.select(
            "Twitter/X İndirme:",
            choices=choices,
            style=custom_style,
            instruction="(↑↓ ile seç, Enter ile onayla)",
        ).ask()

    def ask_twitter_url(self):
        """Twitter/X linki sor."""
        return questionary.text(
            "Twitter/X Video Linki:",
            style=custom_style,
            validate=lambda x: len(x) > 0 or "Link boş olamaz!",
        ).ask()

    def ask_twitter_bulk_file(self):
        """Bulk download dosya yolu sor."""
        return questionary.text(
            "URL listesi dosyası yolunu girin (.txt):",
            style=custom_style,
        ).ask()

    def show_twitter_progress(
        self, current: int, total: int, url: str, success: bool, message: str = ""
    ):
        """Twitter bulk download ilerleme durumu."""
        if "Atlandı" in message:
            status = "[yellow]○[/yellow]"
        elif success:
            status = "[green]✓[/green]"
        else:
            status = "[red]✗[/red]"

        msg_part = f" - {message}" if message else ""
        self.console.print(
            f"{status} [{current}/{total}] {url[:50]}...{msg_part}")

    def show_twitter_summary(
        self, successful: int, failed: int, failed_urls: list, skipped: int = 0
    ):
        """Twitter bulk download özeti."""
        table = Table(show_header=False, box=None)
        table.add_row("[green]✓ İndirildi:[/green]", str(successful))
        if skipped > 0:
            table.add_row(
                "[yellow]○ Atlandı (zaten var):[/yellow]", str(skipped))
        table.add_row("[red]✗ Başarısız:[/red]", str(failed))

        self.console.print(
            Panel(
                table,
                title="[bold cyan]İndirme Özeti[/bold cyan]",
                border_style="cyan",
            )
        )

        if failed_urls:
            self.console.print("\n[yellow]Başarısız URL'ler:[/yellow]")
            for url in failed_urls[:5]:  # İlk 5'ini göster
                self.console.print(f"  [dim]- {url}[/dim]")
            if len(failed_urls) > 5:
                self.console.print(
                    f"  [dim]... ve {len(failed_urls) - 5} tane daha[/dim]")
            self.console.print(
                "\n[dim]Tüm başarısız URL'ler 'failed_downloads.txt' dosyasına kaydedildi.[/dim]")

        if skipped > 0:
            self.console.print(
                "\n[dim]Atlanan videolar daha önce indirilmişti.[/dim]"
            )
