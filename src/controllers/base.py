"""
Base Controller Module
Defines the base class for all UI controllers.
"""

import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from src.utils.logger import get_logger


class BaseController(ABC):
    """Abstract base class for controllers."""

    def __init__(self, config: Any, ui: Any):
        """
        Initialize controller with shared resources.
        
        Args:
            config: Config instance
            ui: Interface instance
        """
        self.config = config
        self.ui = ui
        self.logger = get_logger()

    @abstractmethod
    def run(self) -> None:
        """Main loop for the controller."""

    @staticmethod
    def get_resource_path(relative_path: str) -> Path:
        """
        Get absolute path to resource, works for dev and for PyInstaller bundle.
        """
        if hasattr(sys, "_MEIPASS"):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).resolve().parent.parent.parent
        return base_path / relative_path

    def handle_error(self, e: Exception, context: str) -> None:
        """Centralized error handling for controllers."""
        self.logger.exception(f"Error in {context}", exc=e)
        self.ui.show_error(f"{context} sırasında bir hata oluştu:\n{e}")
        self.ui.wait_for_enter()

    def find_cookie_files(
        self,
        platform_keyword: str = "",
        search_dirs: list[Path] | None = None
    ) -> list[Path]:
        """
        Scan system Downloads, app download folder, current directory, Desktop,
        or provided directories for cookie files (.txt).
        Returns list of existing Paths sorted by modification time (newest first).
        """
        if search_dirs is None:
            search_dirs = [
                Path.home() / "Downloads",
                Path(getattr(self.config, "download_path", Path.home() / "Downloads")),
                Path.cwd(),
                Path.home() / "Desktop"
            ]

        candidates: dict[str, Path] = {}
        keyword = platform_keyword.lower().strip()

        for directory in search_dirs:
            if not directory.exists() or not directory.is_dir():
                continue
            try:
                for file_path in directory.glob("*.txt"):
                    if not file_path.is_file():
                        continue

                    name_lower = file_path.name.lower()
                    is_candidate = False

                    # 1. Match typical cookie naming patterns
                    if "cookie" in name_lower:
                        is_candidate = True
                    elif keyword and keyword in name_lower:
                        is_candidate = True
                    else:
                        # 2. Inspect first line for Netscape cookie header if size is reasonable (<5MB)
                        try:
                            if file_path.stat().st_size < 5 * 1024 * 1024:
                                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                    first_line = f.readline()
                                    if "# Netscape HTTP Cookie File" in first_line or "# HTTP Cookie File" in first_line:
                                        is_candidate = True
                        except Exception:
                            pass

                    if is_candidate:
                        # Filter by platform keyword if specified and file name mentions another platform
                        if keyword:
                            other_platforms = {"youtube", "twitter", "x.com", "tiktok", "facebook"} - {keyword}
                            if any(op in name_lower for op in other_platforms) and keyword not in name_lower:
                                continue
                        candidates[str(file_path.resolve())] = file_path
            except Exception:
                continue

        # Sort by modification time, newest first
        sorted_files = sorted(
            candidates.values(),
            key=lambda p: p.stat().st_mtime if p.exists() else 0,
            reverse=True
        )
        return sorted_files

    def prompt_cookie_file(
        self,
        platform_name: str = "Tüm Platformlar",
        keyword: str = "",
        search_dirs: list[Path] | None = None
    ) -> str | None:
        """
        Interactive cookie file picker. Automatically scans Downloads folder and
        presents detected cookie files with timestamps, or allows manual entry.
        """
        import questionary
        from datetime import datetime

        detected = self.find_cookie_files(keyword, search_dirs=search_dirs)

        if detected:
            self.ui.console.print(
                f"\n[bold green]✓ İndirilenler / sistem klasörlerinde {len(detected)} adet cookie dosyası bulundu![/bold green]\n"
            )

            choices = []
            for idx, path in enumerate(detected[:8]):
                try:
                    mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%d.%m %H:%M")
                    size_kb = f"{path.stat().st_size / 1024:.1f} KB"
                    badge = " [EN YENİ]" if idx == 0 else ""
                    folder_label = "İndirilenler" if "Downloads" in str(path) else path.parent.name
                    label = f"🍪 {path.name} [{folder_label}] ({mtime}, {size_kb}){badge}"
                except Exception:
                    label = f"🍪 {path.name}"
                choices.append(label)

            choices.append("📁 Farklı Bir Dosya Yolu Gir (Manuel)")
            choices.append("🔙 İptal / Geri Dön")

            selected = questionary.select(
                f"{platform_name} için Cookie Dosyası Seçin:",
                choices=choices,
                style=self.ui.custom_style
            ).ask()

            if not selected or "İptal" in selected:
                return None

            if "Manuel" in selected:
                manual_path = questionary.text(
                    "Cookie dosyası tam yolu (.txt):",
                    style=self.ui.custom_style
                ).ask()
                return manual_path.strip() if manual_path else None

            # Find chosen path
            for idx, choice_label in enumerate(choices[:len(detected[:8])]):
                if selected == choice_label:
                    return str(detected[idx])
        else:
            self.ui.console.print("\n[yellow]ℹ İndirilenler klasöründe otomatik cookie dosyası bulunamadı.[/yellow]")
            manual_path = questionary.text(
                f"{platform_name} Cookie dosyası yolu (.txt):",
                style=self.ui.custom_style
            ).ask()
            return manual_path.strip() if manual_path else None

