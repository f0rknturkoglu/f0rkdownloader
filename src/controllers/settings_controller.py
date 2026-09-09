"""
Settings Controller
Handles application configuration UI.
"""

from typing import Any

from src.controllers.base import BaseController


class SettingsController(BaseController):
    """Controller for application settings."""
    
    def __init__(self, config: Any, ui: Any):
        super().__init__(config, ui)
    
    def run(self) -> None:
        """Settings menu loop."""
        self.ui.push_breadcrumb("Ayarlar")
        
        while True:
            self.ui.print_header(self.config.download_path)
            
            import questionary
            choices = [
                f"Tema Değiştir ({self.config.theme_color})",
                f"Video Kalitesi ({self.config.get_quality_display()})",
                f"İndirme Formatı ({self.config.format_type.upper()})",
                f"Eşzamanlı İndirme ({self.config.max_workers} İş Parçacığı)",
                "Ayarları Sıfırla",
                "Geri Dön"
            ]
            
            choice = questionary.select(
                "Uygulama Ayarları:",
                choices=choices,
                style=self.ui.custom_style
            ).ask()
            
            if not choice or "Geri Dön" in choice:
                break
            
            if "Tema" in choice:
                self.handle_theme()
            elif "Kalite" in choice:
                self.handle_quality()
            elif "Format" in choice:
                self.handle_format()
            elif "Eşzamanlı" in choice:
                self.handle_max_workers()
            elif "Sıfırla" in choice:
                self.handle_reset()
                
        self.ui.pop_breadcrumb()

    def handle_theme(self) -> None:
        """Change application theme."""
        import questionary
        themes = ["ubuntu", "macintosh", "fedora"]
        theme = questionary.select(
            "Tema seçin:",
            choices=themes,
            default=self.config.theme_color,
            style=self.ui.custom_style
        ).ask()
        
        if theme:
            self.config.theme_color = theme
            self.config.save()
            self.ui.update_theme(theme)

    def handle_quality(self) -> None:
        """Change video quality."""
        import questionary
        qualities = ["En İyi", "1080p", "720p", "En Düşük"]
        quality = questionary.select(
            "Varsayılan video kalitesi:",
            choices=qualities,
            style=self.ui.custom_style
        ).ask()
        
        if quality:
            self.config.set_quality(quality)
            self.config.save()

    def handle_format(self) -> None:
        """Change download format."""
        import questionary
        fmt = questionary.select(
            "İndirme formatı:",
            choices=["Video (MP4)", "Sadece Ses (MP3)"],
            style=self.ui.custom_style
        ).ask()
        
        if fmt:
            self.config.set_format(fmt)
            self.config.save()

    def handle_max_workers(self) -> None:
        """Change concurrent worker count."""
        import questionary
        choices = [
            "1 (Sıralı / Tek Tek)",
            "2 (Dengeli)",
            "3 (Varsayılan Hızlı)",
            "5 (Maksimum Performans)",
        ]
        worker_choice = questionary.select(
            "Eşzamanlı indirilecek video sayısı:",
            choices=choices,
            style=self.ui.custom_style
        ).ask()
        
        if worker_choice:
            num = int(worker_choice.split()[0])
            self.config.max_workers = num
            self.config.save()
            self.ui.show_success(f"Eşzamanlı indirme {num} iş parçacığı olarak ayarlandı.")
            self.ui.wait_for_enter()

    def handle_reset(self) -> None:
        """Reset settings to default."""
        if self.ui.ask_confirmation("Tüm ayarlar sıfırlansın mı?"):
            self.config.reset()
            self.ui.show_success("Ayarlar sıfırlandı.")
            self.ui.wait_for_enter()
