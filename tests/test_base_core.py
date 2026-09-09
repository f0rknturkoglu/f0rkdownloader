"""
Unit tests for DownloaderBase and custom exceptions in src.core.base.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.core.base import (
    AuthenticationError,
    DownloaderBase,
    DownloaderError,
    DownloadError,
    NetworkError,
    ValidationError,
)


class DummyDownloader(DownloaderBase):
    """Concrete implementation of DownloaderBase for testing."""
    def download(self, url, progress_hooks=None):
        return True, "Success"


class TestBaseCore(unittest.TestCase):
    """Test suite for base downloader and exceptions."""

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
        self.downloader = DummyDownloader(self.config)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_exceptions_hierarchy(self):
        """Test that all specific exceptions inherit from DownloaderError."""
        self.assertTrue(issubclass(AuthenticationError, DownloaderError))
        self.assertTrue(issubclass(DownloadError, DownloaderError))
        self.assertTrue(issubclass(NetworkError, DownloaderError))
        self.assertTrue(issubclass(ValidationError, DownloaderError))
        self.assertTrue(issubclass(DownloaderError, Exception))

    def test_default_headers(self):
        """Test default headers are populated."""
        self.assertIn("User-Agent", self.downloader.default_headers)
        self.assertIn("Mozilla", self.downloader.default_headers["User-Agent"])

    def test_get_base_options_video(self):
        """Test base yt-dlp options for video format."""
        self.config.format_type = "video"
        self.config.quality = "1080p"
        opts = self.downloader.get_base_options()

        self.assertEqual(opts["format"], "1080p")
        self.assertEqual(opts["socket_timeout"], 30)
        self.assertEqual(opts["retries"], 5)
        self.assertEqual(opts["file_access_retries"], 3)
        self.assertEqual(opts["merge_output_format"], "mp4")
        self.assertEqual(opts["postprocessors"][0]["key"], "FFmpegVideoConvertor")
        self.assertEqual(opts["postprocessors"][0]["preferedformat"], "mp4")

    def test_get_base_options_audio(self):
        """Test base yt-dlp options for audio format."""
        self.config.format_type = "audio"
        opts = self.downloader.get_base_options()

        self.assertEqual(opts["postprocessors"][0]["key"], "FFmpegExtractAudio")
        self.assertEqual(opts["postprocessors"][0]["preferredcodec"], "mp3")
        self.assertEqual(opts["postprocessors"][0]["preferredquality"], "192")


if __name__ == "__main__":
    unittest.main()
