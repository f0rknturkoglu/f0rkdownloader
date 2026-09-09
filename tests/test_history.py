"""
Tests for the Download History module.
"""

# Add src to path
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.history import DownloadHistory


class TestDownloadHistory(unittest.TestCase):
    """Test cases for DownloadHistory class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        self.history = DownloadHistory(self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove test files
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_extract_youtube_video_id(self):
        """Test YouTube video ID extraction from various URL formats."""
        test_cases = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLtest", "dQw4w9WgXcQ"),
            ("https://youtube.com/shorts/abcdefghijk", "abcdefghijk"),
        ]
        
        for url, expected_id in test_cases:
            with self.subTest(url=url):
                result = DownloadHistory.extract_video_id(url, "youtube")
                self.assertEqual(result, expected_id)
    
    def test_extract_twitter_video_id(self):
        """Test Twitter video ID extraction from various URL formats."""
        test_cases = [
            ("https://twitter.com/user/status/1234567890123456789", "1234567890123456789"),
            ("https://x.com/user/status/1234567890123456789", "1234567890123456789"),
            ("https://twitter.com/user/status/1234567890123456789?s=20", "1234567890123456789"),
        ]
        
        for url, expected_id in test_cases:
            with self.subTest(url=url):
                result = DownloadHistory.extract_video_id(url, "twitter")
                self.assertEqual(result, expected_id)
    
    def test_extract_tiktok_video_id(self):
        """Test TikTok video ID extraction from various URL formats."""
        test_cases = [
            ("https://www.tiktok.com/@user/video/7123456789012345678", "7123456789012345678"),
            ("https://tiktok.com/@user/video/7123456789012345678?lang=en", "7123456789012345678"),
        ]
        
        for url, expected_id in test_cases:
            with self.subTest(url=url):
                result = DownloadHistory.extract_video_id(url, "tiktok")
                self.assertEqual(result, expected_id)
    
    def test_extract_facebook_video_id(self):
        """Test Facebook video ID extraction from various URL formats."""
        test_cases = [
            ("https://www.facebook.com/watch/?v=123456789012345", "123456789012345"),
            ("https://facebook.com/user/videos/123456789012345", "123456789012345"),
            ("https://www.facebook.com/reel/123456789012345", "123456789012345"),
        ]
        
        for url, expected_id in test_cases:
            with self.subTest(url=url):
                result = DownloadHistory.extract_video_id(url, "facebook")
                self.assertEqual(result, expected_id)
    
    def test_add_download(self):
        """Test adding download to history."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        self.history.add_download(url, "youtube")
        
        is_downloaded, _ = self.history.is_downloaded(url, "youtube")
        self.assertTrue(is_downloaded)
    
    def test_is_downloaded_returns_false_for_new_url(self):
        """Test that is_downloaded returns False for new URLs."""
        url = "https://www.youtube.com/watch?v=newvideo123"
        
        is_downloaded, _ = self.history.is_downloaded(url, "youtube")
        self.assertFalse(is_downloaded)
    
    def test_is_downloaded_returns_true_for_existing_url(self):
        """Test that is_downloaded returns True for existing URLs."""
        url = "https://www.youtube.com/watch?v=existingvid"
        
        self.history.add_download(url, "youtube")
        
        is_downloaded, date = self.history.is_downloaded(url, "youtube")
        self.assertTrue(is_downloaded)
        self.assertIsNotNone(date)
    
    def test_history_persistence(self):
        """Test that history is saved and loaded correctly."""
        url = "https://www.youtube.com/watch?v=persisttest"
        
        self.history.add_download(url, "youtube")
        
        # Create new history instance (simulates app restart)
        new_history = DownloadHistory(self.test_dir)
        
        is_downloaded, _ = new_history.is_downloaded(url, "youtube")
        self.assertTrue(is_downloaded)
    
    def test_multiple_platforms(self):
        """Test adding downloads from multiple platforms."""
        youtube_url = "https://www.youtube.com/watch?v=yttest12345"
        twitter_url = "https://twitter.com/user/status/9876543210123456789"
        tiktok_url = "https://www.tiktok.com/@user/video/1234567890123456789"
        
        self.history.add_download(youtube_url, "youtube")
        self.history.add_download(twitter_url, "twitter")
        self.history.add_download(tiktok_url, "tiktok")
        
        yt_downloaded, _ = self.history.is_downloaded(youtube_url, "youtube")
        tw_downloaded, _ = self.history.is_downloaded(twitter_url, "twitter")
        tt_downloaded, _ = self.history.is_downloaded(tiktok_url, "tiktok")
        
        self.assertTrue(yt_downloaded)
        self.assertTrue(tw_downloaded)
        self.assertTrue(tt_downloaded)
    
    def test_same_video_id_different_urls(self):
        """Test that same video ID is recognized from different URL formats."""
        url1 = "https://www.youtube.com/watch?v=samevidid12"
        url2 = "https://youtu.be/samevidid12"
        
        self.history.add_download(url1, "youtube")
        
        # url2 should be detected as already downloaded
        is_downloaded, _ = self.history.is_downloaded(url2, "youtube")
        self.assertTrue(is_downloaded)
    
    def test_invalid_platform(self):
        """Test handling of invalid platform."""
        url = "https://example.com/video"
        
        # Should not raise an error, just return None for ID
        video_id = DownloadHistory.extract_video_id(url, "invalid_platform")
        self.assertIsNone(video_id)


class TestDownloadHistoryEdgeCases(unittest.TestCase):
    """Edge case tests for DownloadHistory."""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.history = DownloadHistory(self.test_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_empty_url(self):
        """Test handling of empty URL."""
        video_id = DownloadHistory.extract_video_id("", "youtube")
        self.assertIsNone(video_id)
    
    def test_invalid_url_format(self):
        """Test handling of invalid URL format."""
        video_id = DownloadHistory.extract_video_id("not a valid url", "youtube")
        self.assertIsNone(video_id)
    
    def test_url_with_extra_params(self):
        """Test URL with extra query parameters."""
        url = "https://www.youtube.com/watch?v=test1234567&t=120&feature=share"
        
        video_id = DownloadHistory.extract_video_id(url, "youtube")
        self.assertEqual(video_id, "test1234567")

    def test_batch_saving(self):
        """Test auto_save=False does not write immediately until save_history()."""
        url = "https://www.youtube.com/watch?v=batchvid123"
        self.history.add_download(url, "youtube", auto_save=False)
        
        # File shouldn't contain this url yet if we read raw json
        new_hist = DownloadHistory(self.test_dir)
        is_down, _ = new_hist.is_downloaded(url, "youtube")
        self.assertFalse(is_down)
        
        # Now explicitly save
        self.history.save_history()
        new_hist_2 = DownloadHistory(self.test_dir)
        is_down_2, _ = new_hist_2.is_downloaded(url, "youtube")
        self.assertTrue(is_down_2)

    def test_check_file_exists_fallback(self):
        """Test fallback file inspection on disk."""
        platform_dir = Path(self.test_dir) / "YouTube"
        platform_dir.mkdir(parents=True, exist_ok=True)
        sample_file = platform_dir / "my_video_sample12345.mp4"
        sample_file.write_text("dummy")

        hist = DownloadHistory(self.test_dir, platform_paths={"youtube": platform_dir})
        # URL with video ID in name
        url = "https://example.com/custom/sample12345"
        is_down, _ = hist.is_downloaded(url, "youtube")
        self.assertTrue(is_down)


if __name__ == "__main__":
    unittest.main()
