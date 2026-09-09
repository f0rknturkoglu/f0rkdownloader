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


if __name__ == "__main__":
    unittest.main()
