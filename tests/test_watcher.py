"""
Tests for Channel Watcher and tracker.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.utils.channel_watcher import ChannelWatcher


class TestChannelWatcher(unittest.TestCase):
    """Unit tests for ChannelWatcher."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.watcher = ChannelWatcher(Path(self.test_dir))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_add_and_list_targets(self):
        self.assertEqual(len(self.watcher.list_targets()), 0)

        target = self.watcher.add_target(
            url="https://www.youtube.com/@Veritasium",
            platform="youtube",
            name="Veritasium"
        )
        self.assertEqual(target["name"], "Veritasium")
        self.assertEqual(target["platform"], "youtube")
        self.assertEqual(len(self.watcher.list_targets()), 1)

    def test_remove_target(self):
        target = self.watcher.add_target(
            url="https://www.tiktok.com/@mrbeast",
            platform="tiktok",
            name="MrBeast TikTok"
        )
        self.assertEqual(len(self.watcher.list_targets()), 1)

        removed = self.watcher.remove_target(target["id"])
        self.assertTrue(removed)
        self.assertEqual(len(self.watcher.list_targets()), 0)

    @patch("yt_dlp.YoutubeDL")
    def test_scan_target_for_new_videos(self, mock_ydl_cls):
        target = self.watcher.add_target(
            url="https://www.youtube.com/@testchannel",
            platform="youtube",
            name="Test Channel"
        )

        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            "entries": [
                {"url": "https://www.youtube.com/watch?v=vid1"},
                {"url": "https://www.youtube.com/watch?v=vid2"},
            ]
        }
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance

        new_videos = self.watcher.scan_target_for_new_videos(target, limit=5)
        self.assertEqual(len(new_videos), 2)
        self.assertIn("https://www.youtube.com/watch?v=vid1", new_videos)

        # Scanning again should find 0 new videos because they are now in known_videos
        second_scan = self.watcher.scan_target_for_new_videos(target, limit=5)
        self.assertEqual(len(second_scan), 0)


if __name__ == "__main__":
    unittest.main()
