"""
Tests for Format Selector module.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.core.format_selector import FormatSelector


class TestFormatSelector(unittest.TestCase):
    """Unit tests for FormatSelector."""

    @patch("yt_dlp.YoutubeDL")
    def test_extract_available_formats(self, mock_ydl_cls):
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            "title": "Amazing 4K Nature Video",
            "duration": 300,
            "thumbnail": "https://example.com/thumb.jpg",
            "formats": [
                {"format_id": "137", "height": 1080, "vcodec": "avc1.640028", "acodec": "none"},
                {"format_id": "313", "height": 2160, "vcodec": "vp9", "acodec": "none"},
                {"format_id": "140", "height": None, "vcodec": "none", "acodec": "mp4a.40.2"},
            ],
        }
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance

        res = FormatSelector.extract_available_formats("https://youtube.com/watch?v=12345")
        self.assertEqual(res["title"], "Amazing 4K Nature Video")
        self.assertEqual(res["duration"], 300)

        labels = [c["label"] for c in res["choices"]]
        self.assertTrue(any("4K UHD (2160p)" in l for l in labels))
        self.assertTrue(any("Full HD (1080p)" in l for l in labels))
        self.assertTrue(any("MP3 (320 kbps" in l for l in labels))
        self.assertTrue(any("FLAC (Kayıpsız" in l for l in labels))


if __name__ == "__main__":
    unittest.main()
