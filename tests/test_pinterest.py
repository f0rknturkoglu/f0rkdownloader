"""
Tests for Pinterest Downloader and Controller.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.config import Config
from src.core.pinterest import PinterestDownloader
from src.utils.history import DownloadHistory


class TestPinterest(unittest.TestCase):
    """Unit tests for Pinterest downloader and history."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config = Config.__new__(Config)
        self.config.base_download_path = Path(self.test_dir)
        self.config.download_path = str(self.config.base_download_path)
        self.config.pinterest_path = self.config.base_download_path / "Pinterest"
        self.config.pinterest_cookies_file = None
        self.config.max_workers = 2
        self.config._set_defaults()
        self.config._create_directories()
        self.downloader = PinterestDownloader(self.config)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_url_detection(self):
        self.assertTrue(self.downloader.is_pinterest_url("https://www.pinterest.com/pin/123456789/"))
        self.assertTrue(self.downloader.is_pinterest_url("https://pin.it/7xYzW"))
        self.assertFalse(self.downloader.is_pinterest_url("https://youtube.com/watch?v=123"))

    def test_url_normalization(self):
        raw = "https://www.pinterest.com/pin/123456789/?invite_code=abc"
        normalized = self.downloader.normalize_url(raw)
        self.assertEqual(normalized, "https://www.pinterest.com/pin/123456789")

    def test_history_id_extraction(self):
        url = "https://www.pinterest.com/pin/9876543210/"
        video_id = DownloadHistory.extract_video_id(url, "pinterest")
        self.assertEqual(video_id, "9876543210")

        short_url = "https://pin.it/AbC123XyZ"
        short_id = DownloadHistory.extract_video_id(short_url, "pinterest")
        self.assertEqual(short_id, "AbC123XyZ")

    @patch("yt_dlp.YoutubeDL")
    def test_download_success_ytdlp(self, mock_ydl_cls):
        mock_instance = MagicMock()
        mock_instance.download.return_value = 0
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance

        success, msg = self.downloader.download("https://www.pinterest.com/pin/123456789/")
        self.assertTrue(success)
        self.assertIn("Başarıyla", msg)

    @patch("src.core.pinterest.PinterestDownloader._download_with_gallery_dl")
    @patch("yt_dlp.YoutubeDL")
    def test_download_fallback_gallery_dl(self, mock_ydl_cls, mock_gdl):
        mock_instance = MagicMock()
        mock_instance.download.side_effect = Exception("yt-dlp error")
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance

        mock_gdl.return_value = (True, "gallery-dl ile başarıyla indirildi")

        success, msg = self.downloader.download("https://www.pinterest.com/pin/123456789/")
        self.assertTrue(success)
        self.assertIn("gallery-dl", msg)

    def test_read_urls_from_file(self):
        test_file = Path(self.test_dir) / "test_pinterest_urls.txt"
        test_file.write_text(
            "https://www.pinterest.com/pin/111111111/\nhttps://pin.it/222222222/\nhttps://random.com\n",
            encoding="utf-8"
        )
        urls = self.downloader.read_urls_from_file(str(test_file))
        self.assertEqual(len(urls), 2)
        self.assertIn("https://www.pinterest.com/pin/111111111", urls)
        self.assertIn("https://pin.it/222222222", urls)


if __name__ == "__main__":
    unittest.main()
