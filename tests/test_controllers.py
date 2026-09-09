"""
Unit tests for Controllers.
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.controllers.account_controller import AccountController
from src.controllers.base import BaseController
from src.controllers.settings_controller import SettingsController


class ConcreteController(BaseController):
    """Test concrete controller subclass."""
    def run(self):
        pass


class TestControllers(unittest.TestCase):
    """Test suite for controller logic."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config = Config.__new__(Config)
        self.config.base_download_path = Path(self.test_dir)
        self.config.download_path = str(self.config.base_download_path)
        self.config.youtube_path = self.config.base_download_path / "YouTube"
        self.config.twitter_path = self.config.base_download_path / "Twitter"
        self.config.tiktok_path = self.config.base_download_path / "TikTok"
        self.config.facebook_path = self.config.base_download_path / "Facebook"
        self.config.config_file_path = self.config.base_download_path / "settings.json"
        self.config._set_defaults()
        self.config._create_directories()
        self.ui = MagicMock()
        self.base_ctrl = ConcreteController(self.config, self.ui)
        self.settings_ctrl = SettingsController(self.config, self.ui)
        self.account_ctrl = AccountController(self.config, self.ui)
        self.account_ctrl.auth_manager.console = MagicMock()


    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_base_controller_handle_error(self):
        """Test BaseController.handle_error logs and displays error."""
        error = ValueError("Sample test error")
        self.base_ctrl.handle_error(error, "Context Test")
        self.ui.show_error.assert_called_once()
        self.assertIn("Context Test", self.ui.show_error.call_args[0][0])
        self.ui.wait_for_enter.assert_called_once()

    def test_settings_handle_theme(self):
        """Test changing theme via settings controller."""
        with patch("questionary.select") as mock_select:
            mock_select.return_value.ask.return_value = "macintosh"
            self.settings_ctrl.handle_theme()
            self.assertEqual(self.config.theme_color, "macintosh")
            self.ui.update_theme.assert_called_with("macintosh")

    def test_settings_handle_quality(self):
        """Test changing quality via settings controller."""
        with patch("questionary.select") as mock_select:
            mock_select.return_value.ask.return_value = "1080p"
            self.settings_ctrl.handle_quality()
            self.assertIn("1080", self.config.quality)

    def test_settings_handle_format(self):
        """Test changing format via settings controller."""
        with patch("questionary.select") as mock_select:
            mock_select.return_value.ask.return_value = "Sadece Ses (MP3)"
            self.settings_ctrl.handle_format()
            self.assertEqual(self.config.format_type, "audio")

    def test_settings_handle_max_workers(self):
        """Test changing max workers via settings controller."""
        with patch("questionary.select") as mock_select:
            mock_select.return_value.ask.return_value = "5 (Maksimum Hız)"
            self.settings_ctrl.handle_max_workers()
            self.assertEqual(self.config.max_workers, 5)

    def test_settings_handle_reset(self):
        """Test reset settings via settings controller."""
        self.config.theme_color = "fedora"
        self.ui.ask_confirmation.return_value = True
        self.settings_ctrl.handle_reset()
        self.assertEqual(self.config.theme_color, "ubuntu")
        self.ui.show_success.assert_called_once()
        self.ui.wait_for_enter.assert_called_once()

    def test_find_cookie_files_empty(self):
        """Test finding cookie files in empty directory returns empty list."""
        empty_dir = Path(self.test_dir) / "empty_folder"
        empty_dir.mkdir()
        results = self.base_ctrl.find_cookie_files(search_dirs=[empty_dir])
        self.assertEqual(results, [])

    def test_find_cookie_files_detected(self):
        """Test finding cookie files by filename matching."""
        downloads_dir = Path(self.test_dir) / "Downloads"
        downloads_dir.mkdir()
        cookie1 = downloads_dir / "cookies.txt"
        cookie1.write_text("dummy", encoding="utf-8")
        cookie2 = downloads_dir / "twitter_cookies.txt"
        cookie2.write_text("dummy", encoding="utf-8")
        unrelated = downloads_dir / "notes.txt"
        unrelated.write_text("some random note", encoding="utf-8")

        results = self.base_ctrl.find_cookie_files(search_dirs=[downloads_dir])
        self.assertEqual(len(results), 2)
        names = [r.name for r in results]
        self.assertIn("cookies.txt", names)
        self.assertIn("twitter_cookies.txt", names)
        self.assertNotIn("notes.txt", names)

    def test_find_cookie_files_netscape_content(self):
        """Test finding cookie files by Netscape header content."""
        downloads_dir = Path(self.test_dir) / "Downloads_Netscape"
        downloads_dir.mkdir()
        unnamed_cookie = downloads_dir / "export_data.txt"
        unnamed_cookie.write_text("# Netscape HTTP Cookie File\n.google.com TRUE / FALSE 0 SID 123", encoding="utf-8")

        results = self.base_ctrl.find_cookie_files(search_dirs=[downloads_dir])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "export_data.txt")

    def test_prompt_cookie_file_select_detected(self):
        """Test prompt_cookie_file selecting detected file from menu."""
        downloads_dir = Path(self.test_dir) / "Downloads_Prompt"
        downloads_dir.mkdir()
        cookie_file = downloads_dir / "cookies.txt"
        cookie_file.write_text("dummy", encoding="utf-8")

        with patch("questionary.select") as mock_select:
            mock_select.return_value.ask.side_effect = lambda: mock_select.call_args[1]["choices"][0]
            chosen = self.base_ctrl.prompt_cookie_file("YouTube", search_dirs=[downloads_dir])
            self.assertEqual(chosen, str(cookie_file))


    def test_prompt_cookie_file_manual(self):
        """Test prompt_cookie_file falls back to manual entry."""
        empty_dir = Path(self.test_dir) / "Empty_Prompt"
        empty_dir.mkdir()

        with patch("questionary.text") as mock_text:
            mock_text.return_value.ask.return_value = "/manual/path/cookies.txt"
            chosen = self.base_ctrl.prompt_cookie_file("YouTube", search_dirs=[empty_dir])
            self.assertEqual(chosen, "/manual/path/cookies.txt")

    def test_account_controller_auto_scan_empty(self):
        """Test handle_auto_scan_and_connect when no cookies exist."""
        with patch.object(self.account_ctrl, "find_cookie_files", return_value=[]):
            self.account_ctrl.handle_auto_scan_and_connect()
            self.ui.show_error.assert_called_once()
            self.ui.wait_for_enter.assert_called_once()

    def test_account_controller_auto_scan_success(self):
        """Test handle_auto_scan_and_connect when a cookie file exists."""
        cookie_file = Path(self.test_dir) / "cookies.txt"
        cookie_file.write_text("# Netscape HTTP Cookie File", encoding="utf-8")

        with (
            patch.object(self.account_ctrl, "find_cookie_files", return_value=[cookie_file]),
            patch.object(self.account_ctrl, "_apply_universal_cookies") as mock_apply
        ):
            self.account_ctrl.handle_auto_scan_and_connect()
            mock_apply.assert_called_once_with(str(cookie_file))

    def test_find_url_list_files_empty(self):
        """Test finding URL list files in an empty directory."""
        empty_dir = Path(self.test_dir) / "Empty_Urls"
        empty_dir.mkdir()
        results = self.base_ctrl.find_url_list_files(search_dirs=[empty_dir])
        self.assertEqual(results, [])

    def test_find_url_list_files_detected(self):
        """Test finding URL list files by pattern matching and keyword."""
        urls_dir = Path(self.test_dir) / "Downloads_Urls"
        urls_dir.mkdir()
        f1 = urls_dir / "f0rkn_twitter_urls_2026-09-10.txt"
        f1.write_text("https://x.com/user/status/123\n", encoding="utf-8")
        f2 = urls_dir / "tiktok_videos_backup.txt"
        f2.write_text("https://tiktok.com/@u/video/456\n", encoding="utf-8")
        f3 = urls_dir / "cookies.txt"
        f3.write_text("# Netscape HTTP Cookie File", encoding="utf-8")
        f4 = urls_dir / "random_notes.txt"
        f4.write_text("just some text", encoding="utf-8")

        # Search for twitter
        tw_results = self.base_ctrl.find_url_list_files("twitter", search_dirs=[urls_dir])
        self.assertEqual(len(tw_results), 1)
        self.assertEqual(tw_results[0].name, "f0rkn_twitter_urls_2026-09-10.txt")

        # Search all
        all_results = self.base_ctrl.find_url_list_files(search_dirs=[urls_dir])
        names = [r.name for r in all_results]
        self.assertIn("f0rkn_twitter_urls_2026-09-10.txt", names)
        self.assertIn("tiktok_videos_backup.txt", names)
        self.assertNotIn("cookies.txt", names)

    def test_find_url_list_files_content_inspect(self):
        """Test inspecting file content when file name is generic."""
        urls_dir = Path(self.test_dir) / "Content_Urls"
        urls_dir.mkdir()
        unnamed = urls_dir / "custom_batch.txt"
        unnamed.write_text("https://www.youtube.com/watch?v=dQw4w9WgXcQ\n", encoding="utf-8")

        results = self.base_ctrl.find_url_list_files(search_dirs=[urls_dir])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "custom_batch.txt")

    def test_prompt_url_list_file_select_detected(self):
        """Test prompt_url_list_file selecting detected file from menu."""
        urls_dir = Path(self.test_dir) / "Prompt_Urls"
        urls_dir.mkdir()
        url_file = urls_dir / "f0rkn_youtube_urls_2026.txt"
        url_file.write_text("https://www.youtube.com/watch?v=123\n", encoding="utf-8")

        with patch("questionary.select") as mock_select:
            mock_select.return_value.ask.side_effect = lambda: mock_select.call_args[1]["choices"][0]
            chosen = self.base_ctrl.prompt_url_list_file("YouTube", search_dirs=[urls_dir])
            self.assertEqual(chosen, str(url_file))

    def test_prompt_url_list_file_manual(self):
        """Test prompt_url_list_file falls back to manual entry."""
        empty_dir = Path(self.test_dir) / "Empty_Prompt_Urls"
        empty_dir.mkdir()

        with patch("questionary.text") as mock_text:
            mock_text.return_value.ask.return_value = "/manual/path/urls.txt"
            chosen = self.base_ctrl.prompt_url_list_file("YouTube", search_dirs=[empty_dir])
            self.assertEqual(chosen, "/manual/path/urls.txt")


if __name__ == "__main__":
    unittest.main()

