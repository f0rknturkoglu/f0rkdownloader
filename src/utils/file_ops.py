import os
import subprocess
import sys
from rich.tree import Tree
from rich.filesize import decimal
from rich.markup import escape
from rich.text import Text
from pathlib import Path


class FileManager:
    def __init__(self, base_path):
        self.base_path = Path(base_path)

    def get_tree(self):
        """
        İndirme klasörünü tarayıp Rich Tree objesi döndürür.
        """
        tree = Tree(
            f":open_file_folder: [bold orange1]{self.base_path.name}[/bold orange1]",
            guide_style="bold bright_blue",
        )
        self._process_directory(self.base_path, tree)
        return tree

    def _process_directory(self, directory: Path, tree: Tree):
        """
        Klasörü rekürsif olarak tarar ve ağaca ekler.
        """
        # Klasörleri önce, dosyaları sonra sırala
        paths = sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))

        for path in paths:
            # Gizli dosyaları (.DS_Store vb.) atla
            if path.name.startswith("."):
                continue

            if path.is_dir():
                style = "dim" if path.name.startswith("__") else ""
                branch = tree.add(
                    f"[bold orange1]:open_file_folder: {escape(path.name)}[/bold orange1]",
                    style=style,
                    guide_style=style,
                )
                self._process_directory(path, branch)
            else:
                text_filename = Text(path.name, "green")
                text_filename.highlight_regex(r"\..*$", "bold red")
                text_filename.stylize(f"link file://{path}")

                file_size = path.stat().st_size
                text_filename.append(f" ({decimal(file_size)})", "blue")

                icon = (
                    "🎵"
                    if path.suffix in [".mp3", ".m4a", ".wav"]
                    else "🎬"
                    if path.suffix in [".mp4", ".mkv", ".webm"]
                    else "📄"
                )
                tree.add(Text(f"{icon} ") + text_filename)

    def get_all_files(self):
        """
        Kullanıcının seçmesi için 'Klasör/Dosya.mp4' formatında liste döndürür.
        """
        file_list = []
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if file.startswith("."):
                    continue

                full_path = Path(root) / file
                # Base path'e göre göreceli yol
                rel_path = full_path.relative_to(self.base_path)
                file_list.append(str(rel_path))

        return sorted(file_list)

    def open_file(self, relative_path):
        """
        Video/ses dosyalarını IINA ile, diğerlerini varsayılan uygulama ile açar.
        """
        full_path = self.base_path / relative_path

        # Video ve ses uzantıları
        media_extensions = [
            ".mp4",
            ".mkv",
            ".webm",
            ".m4a",
            ".mp3",
            ".wav",
            ".avi",
            ".mov",
        ]

        try:
            if sys.platform == "darwin":  # macOS
                # Medya dosyalarını IINA ile aç
                if full_path.suffix.lower() in media_extensions:
                    iina_path = "/Applications/IINA.app"
                    if os.path.exists(iina_path):
                        subprocess.run(
                            ["open", "-a", "IINA", str(full_path)], check=True
                        )
                    else:
                        # IINA yoksa varsayılan uygulama ile aç
                        subprocess.run(["open", str(full_path)], check=True)
                else:
                    subprocess.run(["open", str(full_path)], check=True)
            elif sys.platform == "win32":  # Windows
                os.startfile(str(full_path))
            else:  # Linux
                subprocess.run(["xdg-open", str(full_path)], check=True)
            return True, f"{full_path.name} açılıyor..."
        except Exception as e:
            return False, str(e)

    def delete_file(self, relative_path):
        """
        Dosyayı siler.
        """
        full_path = self.base_path / relative_path
        try:
            if full_path.exists():
                os.remove(full_path)
                return True, f"{full_path.name} silindi."
            else:
                return False, "Dosya bulunamadı."
        except Exception as e:
            return False, str(e)
