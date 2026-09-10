"""
Tests for Instagram Downloader and Controller.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.config import Config
from src.controllers.instagram_controller import InstagramController
from src.core.instagram import InstagramDownloader
from src.ui.interface import Interface
from src.utils.history import DownloadHistory


class TestInstagram(unittest.TestCase):
    """Unit tests for Instagram downloader and history."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config = Config.__new__(Config)
        self.config.base_download_path = Path(self.test_dir)
        self.config.download_path = str(self.config.base_download_path)
        self.config.instagram_path = self.config.base_download_path / "Instagram"
        self.config.instagram_cookies_file = None
        self.config.max_workers = 2
        self.config._set_defaults()
        self.config._create_directories()
        self.downloader = InstagramDownloader(self.config)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_url_detection(self):
        self.assertTrue(self.downloader.is_instagram_url("https://www.instagram.com/reel/C12345/"))
        self.assertTrue(self.downloader.is_instagram_url("https://instagram.com/p/DF6789/"))
        self.assertFalse(self.downloader.is_instagram_url("https://youtube.com/watch?v=123"))

    def test_url_normalization(self):
        raw = "https://www.instagram.com/reel/C12345/?igsh=abc12345&utm_source=ig_web_copy_link"
        normalized = self.downloader.normalize_url(raw)
        self.assertEqual(normalized, "https://www.instagram.com/reel/C12345")

    def test_history_id_extraction(self):
        url = "https://www.instagram.com/reel/C12345ABC_def/"
        video_id = DownloadHistory.extract_video_id(url, "instagram")
        self.assertEqual(video_id, "C12345ABC_def")

        post_url = "https://instagram.com/p/XYZ987654/"
        post_id = DownloadHistory.extract_video_id(post_url, "instagram")
        self.assertEqual(post_id, "XYZ987654")

    @patch("yt_dlp.YoutubeDL")
    def test_download_success_ytdlp(self, mock_ydl_cls):
        mock_instance = MagicMock()
        mock_instance.download.return_value = 0
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance

        success, msg = self.downloader.download("https://www.instagram.com/reel/C12345/")
        self.assertTrue(success)
        self.assertIn("Başarıyla", msg)

    @patch("src.core.instagram.InstagramDownloader._download_with_gallery_dl")
    @patch("yt_dlp.YoutubeDL")
    def test_download_fallback_gallery_dl(self, mock_ydl_cls, mock_gdl):
        mock_instance = MagicMock()
        mock_instance.download.side_effect = Exception("yt-dlp blocked")
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance

        mock_gdl.return_value = (True, "gallery-dl ile başarıyla indirildi")

        success, msg = self.downloader.download("https://www.instagram.com/reel/C12345/")
        self.assertTrue(success)
        self.assertIn("gallery-dl", msg)

    def test_read_urls_from_file(self):
        test_file = Path(self.test_dir) / "test_instagram_urls.txt"
        test_file.write_text(
            "https://www.instagram.com/reel/C12345/\nhttps://instagram.com/p/ABCDE/\nhttps://google.com\n",
            encoding="utf-8"
        )
        urls = self.downloader.read_urls_from_file(str(test_file))
        self.assertEqual(len(urls), 2)
        self.assertIn("https://www.instagram.com/reel/C12345", urls)
        self.assertIn("https://instagram.com/p/ABCDE", urls)


if __name__ == "__main__":
    unittest.main()
