"""
Tests for Textual TUI Application and Panes.
"""

import tempfile
import unittest
from pathlib import Path

from src.config import Config
from src.ui.tui.app import F0rkDownloaderTUI
from src.ui.tui.panes import (
    AccountsPane,
    BridgePane,
    ClipboardPane,
    HistoryPane,
    PlatformPane,
    SettingsPane,
    WatcherPane,
)


class TestTUI(unittest.TestCase):
    """Unit tests for TUI app and pane composition."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config = Config.__new__(Config)
        self.config.base_download_path = Path(self.test_dir)
        self.config.download_path = str(self.config.base_download_path)
        self.config.youtube_path = self.config.base_download_path / "YouTube"
        self.config.twitter_path = self.config.base_download_path / "Twitter"
        self.config.tiktok_path = self.config.base_download_path / "TikTok"
        self.config.facebook_path = self.config.base_download_path / "Facebook"
        self.config.instagram_path = self.config.base_download_path / "Instagram"
        self.config.pinterest_path = self.config.base_download_path / "Pinterest"
        self.config.config_file_path = self.config.base_download_path / "settings.json"
        self.config._set_defaults()
        self.config._create_directories()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_tui_initialization(self):
        app = F0rkDownloaderTUI(config=self.config)
        self.assertIsNotNone(app)
        self.assertIn("youtube", app.downloaders)
        self.assertIn("tiktok", app.downloaders)
        self.assertIn("twitter", app.downloaders)
        self.assertIn("facebook", app.downloaders)
        self.assertIn("instagram", app.downloaders)
        self.assertIn("pinterest", app.downloaders)
        # Cleanup daemons
        app.on_unmount()

    def test_panes_instantiation(self):
        yt_pane = PlatformPane("youtube", "YouTube")
        tt_pane = PlatformPane("tiktok", "TikTok")
        settings_pane = SettingsPane(self.config)
        accounts_pane = AccountsPane(self.config)
        clip_pane = ClipboardPane()
        watcher_pane = WatcherPane()
        bridge_pane = BridgePane()
        hist_pane = HistoryPane()

        self.assertEqual(yt_pane.platform_key, "youtube")
        self.assertEqual(tt_pane.platform_key, "tiktok")
        self.assertIsNotNone(settings_pane)
        self.assertIsNotNone(accounts_pane)
        self.assertIsNotNone(clip_pane)
        self.assertIsNotNone(watcher_pane)
        self.assertIsNotNone(bridge_pane)
        self.assertIsNotNone(hist_pane)


if __name__ == "__main__":
    unittest.main()
