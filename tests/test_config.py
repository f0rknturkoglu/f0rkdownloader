"""
Tests for the Config module.
"""

# Add src to path
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config


class TestConfig(unittest.TestCase):
    """Test cases for Config class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        
        # Patch the base download path to use temp directory
        self.patcher = patch.object(
            Config, '__init__', 
            lambda self: self._mock_init(self.test_dir)
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_test_config(self):
        """Create a Config instance with mocked paths."""
        config = Config.__new__(Config)
        config.base_download_path = Path(self.test_dir)
        config.download_path = str(config.base_download_path)
        config.youtube_path = config.base_download_path / "YouTube"
        config.twitter_path = config.base_download_path / "Twitter"
        config.tiktok_path = config.base_download_path / "TikTok"
        config.facebook_path = config.base_download_path / "Facebook"
        config.config_file_path = config.base_download_path / "settings.json"
        config._set_defaults()
        config._create_directories()
        return config
    
    def test_default_values(self):
        """Test that defaults are set correctly."""
        config = self._create_test_config()
        
        self.assertEqual(config.theme_color, "ubuntu")
        self.assertEqual(config.format_type, "video")
        self.assertEqual(config.quality, "bestvideo+bestaudio/best")
        self.assertEqual(config.max_workers, 3)
        self.assertIsNone(config.auth_method)
        self.assertIsNone(config.cookies_file)
    
    def test_save_and_load(self):
        """Test saving and loading configuration."""
        config = self._create_test_config()
        
        # Modify settings
        config.theme_color = "macintosh"
        config.format_type = "audio"
        config.twitter_username = "testuser"
        config.max_workers = 5
        
        # Save
        config.save()
        
        # Create new config and load
        new_config = self._create_test_config()
        new_config.load()
        
        self.assertEqual(new_config.theme_color, "macintosh")
        self.assertEqual(new_config.format_type, "audio")
        self.assertEqual(new_config.twitter_username, "testuser")
        self.assertEqual(new_config.max_workers, 5)
    
    def test_set_quality(self):
        """Test quality setting."""
        config = self._create_test_config()
        
        config.set_quality("1080p")
        self.assertIn("1080", config.quality)
        
        config.set_quality("720p")
        self.assertIn("720", config.quality)
        
        config.set_quality("En İyi")
        self.assertEqual(config.quality, "bestvideo+bestaudio/best")
    
    def test_set_format(self):
        """Test format setting."""
        config = self._create_test_config()
        
        config.set_format("Ses (MP3)")
        self.assertEqual(config.format_type, "audio")
        
        config.set_format("Video (MP4)")
        self.assertEqual(config.format_type, "video")
    
    def test_get_quality_display(self):
        """Test quality display string."""
        config = self._create_test_config()
        
        config.quality = "bestvideo+bestaudio/best"
        self.assertEqual(config.get_quality_display(), "En İyi")
        
        config.quality = "some_custom_quality"
        self.assertEqual(config.get_quality_display(), "Özel")
    
    def test_reset(self):
        """Test resetting to defaults."""
        config = self._create_test_config()
        
        # Modify settings
        config.theme_color = "fedora"
        config.twitter_username = "someone"
        
        # Reset
        config.reset()
        
        self.assertEqual(config.theme_color, "ubuntu")
        self.assertIsNone(config.twitter_username)
    
    def test_directories_created(self):
        """Test that directories are created."""
        config = self._create_test_config()
        
        self.assertTrue(config.youtube_path.exists())
        self.assertTrue(config.twitter_path.exists())
        self.assertTrue(config.tiktok_path.exists())
        self.assertTrue(config.facebook_path.exists())
    
    def test_load_invalid_json(self):
        """Test loading corrupted config file."""
        config = self._create_test_config()
        
        # Write invalid JSON
        with open(config.config_file_path, 'w') as f:
            f.write("not valid json {{{")
        
        # Should not raise, just use defaults
        config.load()
        
        self.assertEqual(config.theme_color, "ubuntu")
    
    def test_load_nonexistent_cookie_file(self):
        """Test that nonexistent cookie files are cleared on load."""
        config = self._create_test_config()
        
        # Set a cookie file that doesn't exist
        config.twitter_cookies_file = "/nonexistent/path/cookies.txt"
        config.save()
        
        # Reload
        config.load()
        
        # Should be cleared because file doesn't exist
        self.assertIsNone(config.twitter_cookies_file)


if __name__ == "__main__":
    unittest.main()
