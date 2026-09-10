"""
TUI Modals Module
Provides interactive dialogs for format picking, YouTube search, and file inputs.
"""

from typing import Any
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Input, Label, OptionList, ProgressBar, Static

from src.core.format_selector import FormatSelector


class FormatPickerModal(ModalScreen[dict[str, Any] | None]):
    """Modal for selecting video resolution and codec."""

    CSS = """
    FormatPickerModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #modal-container {
        width: 80;
        height: 24;
        background: #1e293b;
        border: heavy #0284c7;
        padding: 1 2;
    }

    #format-title {
        text-style: bold;
        color: #38bdf8;
        margin-bottom: 1;
    }

    #format-options {
        height: 14;
        border: solid #334155;
        margin-bottom: 1;
    }

    #modal-buttons {
        height: 3;
        align: right middle;
    }

    #modal-buttons Button {
        margin-left: 1;
    }
    """

    def __init__(self, url: str, cookies_file: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.url = url
        self.cookies_file = cookies_file
        self.format_choices: list[dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Label("Format ve Çözünürlük Seçimi", id="format-title")
            yield Label("Seçenekler yükleniyor...", id="status-label")
            yield OptionList(id="format-options")
            with Horizontal(id="modal-buttons"):
                yield Button("İptal", id="btn-cancel", variant="default")
                yield Button("Seç ve İndir", id="btn-select", variant="success")

    def on_mount(self) -> None:
        self.run_worker(self._load_formats, thread=True)

    def _load_formats(self) -> None:
        try:
            data = FormatSelector.extract_available_formats(self.url, self.cookies_file)
            self.format_choices = data.get("choices", [])
            title = data.get("title", "Video")

            def update_ui():
                status_lbl = self.query_one("#status-label", Label)
                status_lbl.update(f"Video: [bold]{title[:65]}...[/bold]")
                opt_list = self.query_one("#format-options", OptionList)
                opt_list.clear_options()
                for c in self.format_choices:
                    opt_list.add_option(c["label"])

            self.app.call_from_thread(update_ui)
        except Exception as e:
            def show_err():
                status_lbl = self.query_one("#status-label", Label)
                status_lbl.update(f"[red]Hata:[/red] {e}")
            self.app.call_from_thread(show_err)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
        elif event.button.id == "btn-select":
            opt_list = self.query_one("#format-options", OptionList)
            if opt_list.highlighted is not None and opt_list.highlighted < len(self.format_choices):
                self.dismiss(self.format_choices[opt_list.highlighted])
            else:
                self.dismiss(None)


class SearchModal(ModalScreen[str | None]):
    """Modal for searching YouTube and selecting a video."""

    CSS = """
    SearchModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #search-container {
        width: 90;
        height: 28;
        background: #1e293b;
        border: heavy #0284c7;
        padding: 1 2;
    }

    #search-bar {
        height: 3;
        margin-bottom: 1;
    }

    #search-input {
        width: 1fr;
        margin-right: 1;
    }

    #results-table {
        height: 16;
        border: solid #334155;
        margin-bottom: 1;
    }

    #search-buttons {
        height: 3;
        align: right middle;
    }

    #search-buttons Button {
        margin-left: 1;
    }
    """

    def __init__(self, youtube_downloader: Any, **kwargs):
        super().__init__(**kwargs)
        self.downloader = youtube_downloader
        self.results: list[dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="search-container"):
            yield Label("[bold cyan]YouTube Arama[/bold cyan]")
            with Horizontal(id="search-bar"):
                yield Input(placeholder="Arama terimi girin...", id="search-input")
                yield Button("Ara", id="btn-do-search", variant="primary")

            yield DataTable(id="results-table")

            with Horizontal(id="search-buttons"):
                yield Button("İptal", id="btn-cancel", variant="default")
                yield Button("Seçilen Videoyu İndir", id="btn-choose", variant="success")

    def on_mount(self) -> None:
        table = self.query_one("#results-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Başlık", "Kanal", "Süre (sn)")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
        elif event.button.id == "btn-do-search":
            inp = self.query_one("#search-input", Input)
            query = inp.value.strip()
            if query:
                self.run_worker(lambda: self._perform_search(query), thread=True)
        elif event.button.id == "btn-choose":
            table = self.query_one("#results-table", DataTable)
            row_idx = table.cursor_row
            if row_idx is not None and row_idx < len(self.results):
                self.dismiss(self.results[row_idx]["url"])
            else:
                self.dismiss(None)

    def _perform_search(self, query: str) -> None:
        results = self.downloader.search(query, max_results=10)
        self.results = results

        def update_table():
            table = self.query_one("#results-table", DataTable)
            table.clear()
            for r in results:
                table.add_row(r["title"][:50], r["channel"][:20], str(r["duration"]))

        self.app.call_from_thread(update_table)


class FilePromptModal(ModalScreen[str | None]):
    """Modal for entering or selecting a URL list file path."""

    CSS = """
    FilePromptModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #file-container {
        width: 75;
        height: 18;
        background: #1e293b;
        border: heavy #0284c7;
        padding: 1 2;
    }

    #file-input {
        margin-bottom: 1;
    }

    #file-buttons {
        height: 3;
        align: right middle;
    }

    #file-buttons Button {
        margin-left: 1;
    }
    """

    def __init__(self, prompt_text: str = "Dosya Yolu Girin:", default_path: str = "", **kwargs):
        super().__init__(**kwargs)
        self.prompt_text = prompt_text
        self.default_path = default_path

    def compose(self) -> ComposeResult:
        with Vertical(id="file-container"):
            yield Label(f"[bold cyan]{self.prompt_text}[/bold cyan]")
            yield Input(value=self.default_path, placeholder="C:\\path\\to\\file.txt", id="file-input")
            with Horizontal(id="file-buttons"):
                yield Button("İptal", id="btn-cancel", variant="default")
                yield Button("Tamam", id="btn-confirm", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
        elif event.button.id == "btn-confirm":
            val = self.query_one("#file-input", Input).value.strip().strip('"').strip("'")
            self.dismiss(val if val else None)
