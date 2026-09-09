"""
Unit tests for AuthManager.
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.core.auth import AuthManager


class TestAuthManager(unittest.TestCase):
    """Test suite for AuthManager."""

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
        self.auth = AuthManager(self.config)
        self.auth.console = MagicMock()


    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_logout(self):
        """Test logout clears all authentication parameters."""
        self.config.auth_method = "browser"
        self.config.browser = "chrome"
        self.config.cookies_file = "cookies.txt"
        self.config.channel_name = "TestChannel"

        result = self.auth.logout()
        self.assertTrue(result)
        self.assertIsNone(self.config.auth_method)
        self.assertIsNone(self.config.browser)
        self.assertIsNone(self.config.cookies_file)
        self.assertIsNone(self.config.channel_name)

    def test_validate_cookies_file_not_found(self):
        """Test validation fails if file does not exist."""
        result = self.auth.validate_cookies_file("nonexistent_path_to_cookies.txt")
        self.assertFalse(result)

    def test_validate_cookies_file_success(self):
        """Test validation succeeds with valid entries."""
        cookie_file = Path(self.test_dir) / "test_cookies.txt"
        cookie_file.write_text("# Netscape HTTP Cookie File\n.youtube.com TRUE / FALSE 0 SID test", encoding="utf-8")

        mock_info = {"entries": [{"title": "Watch Later", "url": "https://youtube.com/playlist?list=WL"}]}
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.return_value = mock_info
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

            with patch.object(self.auth, "get_channel_name_from_cookies_file", return_value="My Channel"):
                result = self.auth.validate_cookies_file(str(cookie_file))
                self.assertTrue(result)
                self.assertEqual(self.config.auth_method, "cookies_file")
                self.assertEqual(self.config.cookies_file, str(cookie_file))
                self.assertEqual(self.config.channel_name, "My Channel")

    def test_validate_cookies_file_invalid(self):
        """Test validation fails if yt-dlp extracts no entries and no title."""
        cookie_file = Path(self.test_dir) / "empty_cookies.txt"
        cookie_file.write_text("dummy", encoding="utf-8")

        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.return_value = {}
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

            result = self.auth.validate_cookies_file(str(cookie_file))
            self.assertFalse(result)

    def test_validate_cookies_file_exception(self):
        """Test validation handles exceptions gracefully."""
        cookie_file = Path(self.test_dir) / "corrupt_cookies.txt"
        cookie_file.write_text("dummy", encoding="utf-8")

        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.side_effect = Exception("Cookie error")
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

            result = self.auth.validate_cookies_file(str(cookie_file))
            self.assertFalse(result)

    def test_validate_browser_cookies_success(self):
        """Test browser cookie validation when yt-dlp finds valid library entries."""
        mock_info = {"entries": [{"title": "Favorites", "url": "https://youtube.com/playlist?list=FL"}]}
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.return_value = mock_info
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

            with patch.object(self.auth, "get_channel_name", return_value="TestUser"):
                result = self.auth.validate_browser_cookies("chrome")
                self.assertTrue(result)
                self.assertEqual(self.config.auth_method, "browser")
                self.assertEqual(self.config.browser, "chrome")
                self.assertEqual(self.config.channel_name, "TestUser")

    def test_validate_browser_cookies_failure(self):
        """Test browser cookie validation failure when no entries found."""
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.return_value = None
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

            result = self.auth.validate_browser_cookies("firefox")
            self.assertFalse(result)

    def test_validate_browser_cookies_exception(self):
        """Test browser cookie validation handles exception."""
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.side_effect = RuntimeError("Browser lock")
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

            result = self.auth.validate_browser_cookies("chrome")
            self.assertFalse(result)

    def test_get_channel_name_from_cookies_file(self):
        """Test retrieving channel name from cookies file."""
        mock_info = {"channel": "Awesome Creator"}
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.return_value = mock_info
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

            name = self.auth.get_channel_name_from_cookies_file("fake.txt")
            self.assertEqual(name, "Awesome Creator")

    def test_get_channel_name_from_cookies_file_exception(self):
        """Test retrieving channel name gracefully returns None on error."""
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.side_effect = Exception("Network fail")
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

            name = self.auth.get_channel_name_from_cookies_file("fake.txt")
            self.assertIsNone(name)

    def test_get_channel_name_from_browser(self):
        """Test retrieving channel name using browser cookies."""
        mock_info = {"uploader": "UploaderName"}
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.return_value = mock_info
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

            name = self.auth.get_channel_name("chrome")
            self.assertEqual(name, "UploaderName")

    def test_get_user_playlists_unauthenticated(self):
        """Test get_user_playlists returns empty list when unauthenticated."""
        self.config.auth_method = None
        playlists = self.auth.get_user_playlists()
        self.assertEqual(playlists, [])

    def test_get_user_playlists_cookies_file(self):
        """Test get_user_playlists with cookies_file authentication."""
        self.config.auth_method = "cookies_file"
        self.config.cookies_file = "my_cookies.txt"

        mock_info = {
            "entries": [
                {"title": "Music", "url": "https://youtube.com/playlist?list=1"},
                {"title": "", "url": "https://youtube.com/playlist?list=2"},
                {"title": "Podcasts", "url": "https://youtube.com/playlist?list=3"},
            ]
        }
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.return_value = mock_info
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

            playlists = self.auth.get_user_playlists()
            self.assertEqual(len(playlists), 2)
            self.assertEqual(playlists[0]["title"], "Music")
            self.assertEqual(playlists[1]["title"], "Podcasts")

    def test_get_user_playlists_browser(self):
        """Test get_user_playlists with browser authentication."""
        self.config.auth_method = "browser"
        self.config.browser = "firefox"

        mock_info = {
            "entries": [
                {"title": "Watch Later", "url": "https://youtube.com/playlist?list=WL"}
            ]
        }
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.return_value = mock_info
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

            playlists = self.auth.get_user_playlists()
            self.assertEqual(len(playlists), 1)
            self.assertEqual(playlists[0]["title"], "Watch Later")

    def test_get_user_playlists_exception(self):
        """Test get_user_playlists returns empty list on exception."""
        self.config.auth_method = "browser"
        self.config.browser = "edge"

        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.side_effect = Exception("Timeout")
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

            playlists = self.auth.get_user_playlists()
            self.assertEqual(playlists, [])


if __name__ == "__main__":
    unittest.main()
