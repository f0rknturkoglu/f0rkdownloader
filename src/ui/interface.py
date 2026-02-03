import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import questionary
from src.ui.theme import get_style, get_colors
from typing import Callable, Any

console = Console()


# Sabit UI sembolleri (Temiz Görünüm)
class Icons:
    BACK = "‹"
    FORWARD = "›"
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
    YOUTUBE = "▶"
    TWITTER = "🐦"
    TIKTOK = "🎵"
    FACEBOOK = "📘"
    CONNECTED = "●"
    DISCONNECTED = "○"
    ARROW = "➜"
    DOT = "•"


class Interface:
    def __init__(self):
        self.console = console
        self.breadcrumb: list[str] = []
        # Varsayılan tema (Turuncu)
        self.colors = get_colors("orange")
        self.custom_style = get_style("orange")

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")
        
    def update_theme(self, theme_name: str):
        """Temayı güncelle."""
        self.colors = get_colors(theme_name)
        self.custom_style = get_style(theme_name)

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
        
        # Temiz ASCII Art (Renksiz)
        banner_text = """
 ███████╗ ██████╗ ██████╗ ██╗  ██╗███╗   ██╗
 ██╔════╝██╔═████╗██╔══██╗██║ ██╔╝████╗  ██║
 █████╗  ██║██╔██║██████╔╝█████╔╝ ██╔██╗ ██║
 ██╔══╝  ████╔╝██║██╔══██╗██╔═██╗ ██║╚██╗██║
 ██║     ╚██████╔╝██║  ██║██║  ██╗██║ ╚████║
 ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
"""
        # Banner'ı dinamik renklendir
        colored_banner = f"[bold {self.colors['primary']}]{banner_text}[/bold {self.colors['primary']}]"
        
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        
        # Banner
        grid.add_row(colored_banner)
        grid.add_row(
             f"[bold white]PREMIUM DOWNLOADER[/bold white] │ [dim]v2.1[/dim]"
        )
        grid.add_row("")  # Spacer

        # Breadcrumb göster
        if self.breadcrumb:
            breadcrumb_items = []
            for b in self.breadcrumb:
                breadcrumb_items.append(f"[bold {self.colors['secondary']}]{b}[/bold {self.colors['secondary']}]")
            
            breadcrumb_text = " › ".join(breadcrumb_items)
            
            grid.add_row(
                Panel(
                    breadcrumb_text,
                    style=self.colors['secondary'],
                    border_style=self.colors['secondary'],
                    padding=(0, 2)
                )
            )
        
        # İndirme konumu
        grid.add_row(
            f"[dim]📁 {download_path}[/dim]"
        )

        self.console.print(
            Panel(
                grid,
                border_style=self.colors['primary'],
                padding=(1, 2)
            )
        )

    def show_success(self, message: str):
        self.console.print(
            Panel(
                f"[bold {self.colors['success']}]{Icons.SUCCESS} {message}[/bold {self.colors['success']}]",
                border_style=self.colors['success'],
            )
        )

    def show_error(self, message: str):
        self.console.print(
            Panel(
                f"[bold {self.colors['error']}]{Icons.ERROR} Hata:[/bold {self.colors['error']}]\n{message}",
                border_style=self.colors['error'],
            )
        )

    def show_warning(self, message: str):
        """Uyarı mesajı göster."""
        self.console.print(f"[{self.colors['warning']}]{Icons.SKIP} {message}[/{self.colors['warning']}]")

    def show_info(self, message: str):
        """Bilgi mesajı göster."""
        self.console.print(f"[{self.colors['info']}]ℹ {message}[/{self.colors['info']}]")

    def wait_for_enter(self, message: str = "Devam etmek için Enter..."):
        """Enter bekle."""
        self.console.print(f"\n[dim]{message}[/dim]")
        questionary.text("", qmark="", style=self.custom_style).ask()

    def ask_main_menu(self, stats: dict | None = None) -> str:
        """Ana menü - gruplandırılmış."""
        choices = [
            f"{Icons.YOUTUBE}  YouTube",
            f"{Icons.TIKTOK}  TikTok",
            f"{Icons.TWITTER}  Twitter/X",
            f"{Icons.FACEBOOK}  Facebook",
            f"{Icons.SETTINGS}  Ayarlar",
            f"{Icons.ACCOUNT}  Hesap İşlemleri",
            f"{Icons.EXIT}  Çıkış",
        ]

        return questionary.select(
            "Ne yapmak istersiniz?",
            choices=choices,
            style=self.custom_style,
            instruction="(yukari/asagi ile sec, Enter ile onayla)",
        ).ask()

    def ask_youtube_menu(self) -> str:
        """YouTube İşlemleri Menüsü."""
        choices = [
            f"{Icons.DOWNLOAD}  Link ile İndir (Video/Playlist)",
            f"{Icons.SEARCH}  YouTube'da Ara",
            f"{Icons.FOLDER}  Kütüphanemden İndir (Özel Playlistler)",
            f"{Icons.FOLDER}  İndirilenleri Yönet",
            f"{Icons.BACK}  Geri Dön",
        ]
        return questionary.select(
            "YouTube İşlemleri:",
            choices=choices,
            style=self.custom_style,
        ).ask()

    def ask_confirmation(self, message: str) -> bool:
        """Ask for yes/no confirmation."""
        return questionary.confirm(
            message,
            default=True,
            style=self.custom_style,
        ).ask()

    def show_url_extraction_script(self, script: str) -> None:
        """Show JavaScript for URL extraction."""
        self.console.print("\n[bold yellow]Bu scripti tarayıcı konsolunda (F12) çalıştırın:[/bold yellow]")
        self.console.print(
            Panel(
                f"[white]{script.strip()}[/white]",
                border_style="yellow",
                title="İndirme Scripti",
                padding=(1, 2)
            )
        )

    def show_twitter_progress(self, current: int, total: int, url: str, success: bool, msg: str) -> None:
        """Show Twitter bulk download progress."""
        status = f"[green]Tamamlandı[/green]" if success else f"[red]Hata: {msg}[/red]"
        if "Atlandı" in msg:
            status = f"[yellow]Atlandı[/yellow]"
        
        self.console.print(f"[dim][{current}/{total}][/dim] {url[:50]}... -> {status}")

    def show_twitter_summary(self, successful: int, failed: int, failed_urls: list[str], skipped: int = 0) -> None:
        """Show summary of bulk download."""
        table = Table(title="İndirme Özeti", show_header=True, header_style="bold magenta")
        table.add_column("Durum", style="dim")
        table.add_column("Adet", justify="right")
        
        table.add_row("Başarılı", f"[green]{successful}[/green]")
        table.add_row("Hatalı", f"[red]{failed}[/red]")
        table.add_row("Atlanan (Mevcut)", f"[yellow]{skipped}[/yellow]")
        
        self.console.print("\n")
        self.console.print(table)
        
        if failed_urls:
            self.console.print("\n[red]Hatalı URL'ler:[/red]")
            for f_url in failed_urls:
                self.console.print(f"- {f_url}")
