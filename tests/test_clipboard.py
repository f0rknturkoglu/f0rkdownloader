"""
Tests for Clipboard Watcher and URL detection.
"""

import unittest
from unittest.mock import patch
from src.utils.clipboard_watcher import ClipboardWatcher


class TestClipboardWatcher(unittest.TestCase):
    """Unit tests for clipboard watcher."""

    def setUp(self):
        self.watcher = ClipboardWatcher()

    def test_detect_platforms(self):
        # YouTube
        res = self.watcher.detect_platform("Check out this video https://www.youtube.com/watch?v=dQw4w9WgXcQ amazing")
        self.assertIsNotNone(res)
        self.assertEqual(res[1], "youtube")

        # Twitter
        res = self.watcher.detect_platform("https://x.com/username/status/1234567890123456789")
        self.assertIsNotNone(res)
        self.assertEqual(res[1], "twitter")

        # TikTok
        res = self.watcher.detect_platform("https://www.tiktok.com/@creator/video/7123456789012345678")
        self.assertIsNotNone(res)
        self.assertEqual(res[1], "tiktok")

        # Facebook
        res = self.watcher.detect_platform("https://www.facebook.com/watch/?v=987654321")
        self.assertIsNotNone(res)
        self.assertEqual(res[1], "facebook")

        # Instagram
        res = self.watcher.detect_platform("https://www.instagram.com/reel/C12345ABC/")
        self.assertIsNotNone(res)
        self.assertEqual(res[1], "instagram")

        # Pinterest
        res = self.watcher.detect_platform("https://www.pinterest.com/pin/123456789012/")
        self.assertIsNotNone(res)
        self.assertEqual(res[1], "pinterest")

        # Non-video / Invalid text
        res = self.watcher.detect_platform("Just regular clipboard text without any supported link")
        self.assertIsNone(res)

    def test_start_and_stop(self):
        with patch("pyperclip.paste", return_value=""):
            started = self.watcher.start()
            self.assertTrue(started)
            self.assertTrue(self.watcher.is_running)

            self.watcher.stop()
            self.assertFalse(self.watcher.is_running)


if __name__ == "__main__":
    unittest.main()
