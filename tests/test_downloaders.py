"""
Unit tests for platform downloaders, AuthManager, and UI interface.
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.controllers.base import BaseController
from src.core.auth import AuthManager
from src.core.facebook import FacebookDownloader
from src.core.tiktok import TikTokDownloader
from src.core.twitter import TwitterDownloader
from src.core.youtube import YoutubeDownloader
from src.ui.interface import Interface


class BaseDownloaderTestCase(unittest.TestCase):
    """Base test case setting up temp dirs and mock config."""

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

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)


class TestYoutubeDownloader(BaseDownloaderTestCase):
    """Tests for YoutubeDownloader."""

    def test_search(self):
        downloader = YoutubeDownloader(self.config)
        mock_info = {
            "entries": [
                {
                    "title": "Test Video",
                    "url": "https://youtube.com/watch?v=123",
                    "duration": 120,
                    "channel": "Test Channel",
                    "view_count": 1000,
                }
            ]
        }
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.return_value = mock_info
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
            
            results = downloader.search("test query", max_results=1)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["title"], "Test Video")

    def test_download_success(self):
        downloader = YoutubeDownloader(self.config)
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.download.return_value = 0
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
            
            success, msg = downloader.download("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            self.assertTrue(success)
            self.assertIn("başarılı", msg.lower())

    def test_download_duplicate(self):
        downloader = YoutubeDownloader(self.config)
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        downloader.history.add_download(url, "youtube")
        
        success, msg = downloader.download(url)
        self.assertFalse(success)
        self.assertIn("zaten indirilmiş", msg)

    def test_find_ffmpeg_caching(self):
        downloader = YoutubeDownloader(self.config)
        fake_ffmpeg = str(Path(self.test_dir) / "bin" / "ffmpeg")
        expected_dir = str(Path(self.test_dir) / "bin")
        with patch("shutil.which", return_value=fake_ffmpeg) as mock_which:
            path1 = downloader._find_ffmpeg()
            self.assertEqual(path1, expected_dir)
            self.assertEqual(mock_which.call_count, 1)

            # Second call should use cache, call_count should still be 1
            path2 = downloader._find_ffmpeg()
            self.assertEqual(path2, expected_dir)
            self.assertEqual(mock_which.call_count, 1)


    def test_read_urls_from_file(self):
        downloader = YoutubeDownloader(self.config)
        test_file = Path(self.test_dir) / "yt_urls.txt"
        test_file.write_text(
            "https://www.youtube.com/watch?v=12345678901\n"
            "invalid_line\n"
            "https://youtu.be/abcdefghijk\n",
            encoding="utf-8"
        )
        urls = downloader.read_urls_from_file(str(test_file))
        self.assertEqual(len(urls), 2)
        self.assertIn("https://www.youtube.com/watch?v=12345678901", urls)
        self.assertIn("https://youtu.be/abcdefghijk", urls)

    def test_read_urls_from_directory_path(self):
        downloader = YoutubeDownloader(self.config)
        sub_dir = Path(self.test_dir) / "yt_url_folder"
        sub_dir.mkdir()
        test_file = sub_dir / "f0rkn_youtube_urls_2026.txt"
        test_file.write_text("https://www.youtube.com/watch?v=12345678901\n", encoding="utf-8")
        urls = downloader.read_urls_from_file(str(sub_dir))
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], "https://www.youtube.com/watch?v=12345678901")

    def test_bulk_download(self):
        downloader = YoutubeDownloader(self.config)
        urls = [
            "https://www.youtube.com/watch?v=12345678901",
            "https://www.youtube.com/watch?v=abcdefghijk"
        ]
        with patch.object(downloader, "download", return_value=(True, "İndirme başarılı!")):
            successful, failed, skipped, failed_urls = downloader.bulk_download(urls)
            self.assertEqual(successful, 2)
            self.assertEqual(failed, 0)
            self.assertEqual(skipped, 0)
            self.assertEqual(failed_urls, [])

    def test_download_error_handling(self):
        downloader = YoutubeDownloader(self.config)
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.download.side_effect = Exception("Download failed")
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

            success, msg = downloader.download("https://www.youtube.com/watch?v=12345678901")
            self.assertFalse(success)
            self.assertIn("Download failed", msg)

    def test_bulk_download_with_failures(self):
        downloader = YoutubeDownloader(self.config)
        urls = [
            "https://www.youtube.com/watch?v=11111111111",
            "https://www.youtube.com/watch?v=22222222222",
            "https://www.youtube.com/watch?v=33333333333",
        ]
        downloader.history.add_download(urls[2], "youtube")
        with patch.object(downloader, "download", side_effect=[
            (True, "İndirme başarılı!"),
            (False, "Hata oluştu"),
        ]):
            successful, failed, skipped, failed_urls = downloader.bulk_download(urls)
            self.assertEqual(successful, 1)
            self.assertEqual(failed, 1)
            self.assertEqual(skipped, 1)
            self.assertTrue(any(urls[1] in f for f in failed_urls))

    def test_download_fallback_without_cookies_on_error_code(self):
        """Test that cookie-authenticated failure triggers anonymous fallback."""
        self.config.auth_method = "cookies_file"
        self.config.cookies_file = "dummy_cookies.txt"
        downloader = YoutubeDownloader(self.config)

        mock_ydl_with_cookie = MagicMock()
        mock_ydl_with_cookie.download.return_value = 1  # Code 1 (e.g. page reload error)

        mock_ydl_fallback = MagicMock()
        mock_ydl_fallback.download.return_value = 0  # Fallback succeeds

        with patch("yt_dlp.YoutubeDL", side_effect=[
            MagicMock(__enter__=MagicMock(return_value=mock_ydl_with_cookie)),
            MagicMock(__enter__=MagicMock(return_value=mock_ydl_fallback)),
        ]):
            success, msg = downloader.download("https://www.youtube.com/watch?v=12345678901")
            self.assertTrue(success)
            self.assertIn("anonim modda", msg)

    def test_download_fallback_without_cookies_on_exception(self):
        """Test that cookie-authenticated exception triggers anonymous fallback."""
        self.config.auth_method = "cookies_file"
        self.config.cookies_file = "dummy_cookies.txt"
        downloader = YoutubeDownloader(self.config)

        mock_ydl_with_cookie = MagicMock()
        mock_ydl_with_cookie.download.side_effect = Exception("The page needs to be reloaded.")

        mock_ydl_fallback = MagicMock()
        mock_ydl_fallback.download.return_value = 0

        with patch("yt_dlp.YoutubeDL", side_effect=[
            MagicMock(__enter__=MagicMock(return_value=mock_ydl_with_cookie)),
            MagicMock(__enter__=MagicMock(return_value=mock_ydl_fallback)),
        ]):
            success, msg = downloader.download("https://www.youtube.com/watch?v=12345678901")
            self.assertTrue(success)
            self.assertIn("anonim modda", msg)




class TestTwitterDownloader(BaseDownloaderTestCase):
    """Tests for TwitterDownloader."""

    def test_download_gallery_dl_not_found(self):
        downloader = TwitterDownloader(self.config)
        with patch("shutil.which", return_value=None):
            success, msg = downloader.download("https://x.com/user/status/123")
            self.assertFalse(success)
            self.assertIn("gallery-dl", msg)

    def test_download_success(self):
        downloader = TwitterDownloader(self.config)
        with (
            patch("shutil.which", return_value="/usr/bin/gallery-dl"),
            patch("subprocess.run") as mock_run
        ):
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            success, _ = downloader.download("https://x.com/user/status/9876543210123456789")
            self.assertTrue(success)

    def test_read_urls_from_file(self):
        downloader = TwitterDownloader(self.config)
        test_file = Path(self.test_dir) / "twitter_urls.txt"
        test_file.write_text(
            "https://twitter.com/user/status/123\nhttps://x.com/user/status/456\nhttp://other.com/789\n",
            encoding="utf-8"
        )
        urls = downloader.read_urls_from_file(str(test_file))
        self.assertEqual(len(urls), 2)

    def test_read_urls_from_directory_path(self):
        downloader = TwitterDownloader(self.config)
        sub_dir = Path(self.test_dir) / "twitter_url_folder"
        sub_dir.mkdir()
        test_file = sub_dir / "f0rkn_twitter_urls_2026.txt"
        test_file.write_text("https://x.com/user/status/111222333\n", encoding="utf-8")
        urls = downloader.read_urls_from_file(str(sub_dir))
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], "https://x.com/user/status/111222333")

    def test_bulk_download(self):
        downloader = TwitterDownloader(self.config)
        urls = ["https://x.com/user/status/111", "https://x.com/user/status/222"]
        with patch.object(downloader, "download", return_value=(True, "Success")):
            successful, failed, skipped, failed_urls = downloader.bulk_download(urls)
            self.assertEqual(successful, 2)
            self.assertEqual(failed, 0)
            self.assertEqual(skipped, 0)
            self.assertEqual(failed_urls, [])

    def test_download_failure_nonzero_code(self):
        downloader = TwitterDownloader(self.config)
        with (
            patch("shutil.which", return_value="/usr/bin/gallery-dl"),
            patch("subprocess.run") as mock_run
        ):
            mock_run.return_value = MagicMock(returncode=1, stderr="Twitter error 404")
            success, msg = downloader.download("https://x.com/user/status/111")

            self.assertFalse(success)
            self.assertIn("gallery-dl", msg)




class TestTikTokDownloader(BaseDownloaderTestCase):
    """Tests for TikTokDownloader."""

    def test_is_tiktok_url(self):
        downloader = TikTokDownloader(self.config)
        self.assertTrue(downloader.is_tiktok_url("https://www.tiktok.com/@user/video/123"))
        self.assertTrue(downloader.is_tiktok_url("https://vm.tiktok.com/abc"))
        self.assertFalse(downloader.is_tiktok_url("https://youtube.com/watch?v=123"))

    def test_download_success(self):
        downloader = TikTokDownloader(self.config)
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.download.return_value = 0
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
            
            success, _ = downloader.download("https://www.tiktok.com/@user/video/1234567890123456789")
            self.assertTrue(success)

    def test_save_failed_urls_does_not_crash(self):
        downloader = TikTokDownloader(self.config)
        downloader._save_failed_urls(["https://www.tiktok.com/@user/video/failed123"])
        files = list(downloader.tiktok_download_path.glob("failed_downloads_*.txt"))
        self.assertGreaterEqual(len(files), 1)

    def test_read_urls_from_directory_path(self):
        downloader = TikTokDownloader(self.config)
        sub_dir = Path(self.test_dir) / "tiktok_url_folder"
        sub_dir.mkdir()
        test_file = sub_dir / "f0rkn_tiktok_urls_2026.txt"
        test_file.write_text("https://www.tiktok.com/@user/video/777888999\n", encoding="utf-8")
        urls = downloader.read_urls_from_file(str(sub_dir))
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], "https://www.tiktok.com/@user/video/777888999")

    def test_bulk_download(self):
        downloader = TikTokDownloader(self.config)
        urls = ["https://www.tiktok.com/@user/video/111", "https://www.tiktok.com/@user/video/222"]
        with patch.object(downloader, "download", return_value=(True, "Başarıyla indirildi")):
            successful, failed, skipped, failed_urls = downloader.bulk_download(urls)
            self.assertEqual(successful, 2)
            self.assertEqual(failed, 0)
            self.assertEqual(skipped, 0)
            self.assertEqual(failed_urls, [])

    def test_normalize_tiktok_url(self):
        downloader = TikTokDownloader(self.config)
        # Direct URL without @username
        norm1 = downloader.normalize_url("https://www.tiktok.com/video/7618739710869032213")
        self.assertEqual(norm1, "https://www.tiktok.com/@video/video/7618739710869032213")

        # URL with @username
        norm2 = downloader.normalize_url("https://www.tiktok.com/@user/video/7618739710869032213")
        self.assertEqual(norm2, "https://www.tiktok.com/@user/video/7618739710869032213")

        # URL with tracking parameters
        norm3 = downloader.normalize_url("https://www.tiktok.com/video/7618739710869032213?is_from_webapp=1")
        self.assertEqual(norm3, "https://www.tiktok.com/@video/video/7618739710869032213")

    def test_download_gallery_dl_fallback_on_ytdlp_fail(self):
        downloader = TikTokDownloader(self.config)
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.download.side_effect = Exception("yt-dlp anti-bot")
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

            with patch.object(downloader, "_download_with_gallery_dl", return_value=(True, "gallery-dl success")) as mock_gdl:
                success, msg = downloader.download("https://www.tiktok.com/@user/video/999")
                self.assertTrue(success)
                self.assertIn("gallery-dl", msg)
                mock_gdl.assert_called_once()

    def test_download_error_handling(self):
        downloader = TikTokDownloader(self.config)
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.download.side_effect = Exception("yt-dlp fail")
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

            with patch.object(downloader, "_download_with_gallery_dl", return_value=(False, "gallery-dl fail")):
                success, msg = downloader.download("https://www.tiktok.com/@user/video/999")
                self.assertFalse(success)
                self.assertIn("hata", msg.lower())



class TestFacebookDownloader(BaseDownloaderTestCase):
    """Tests for FacebookDownloader."""

    def test_extract_video_id(self):
        downloader = FacebookDownloader(self.config)
        vid = downloader._extract_video_id("https://www.facebook.com/watch/?v=123456789")
        self.assertEqual(vid, "123456789")

    def test_download_video_direct(self):
        downloader = FacebookDownloader(self.config)
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_response.__enter__.return_value = mock_response
        
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session.__enter__.return_value = mock_session

        with patch.object(downloader, "_load_cookies_to_session", return_value=mock_session):
            success, msg = downloader._download_video_direct(
                "https://fbcdn.net/video.mp4",
                "12345",
                original_url="https://facebook.com/watch/?v=12345"
            )
            self.assertTrue(success)
            self.assertIn("Başarıyla", msg)
            is_down, _ = downloader.history.is_downloaded("https://facebook.com/watch/?v=12345", "facebook")
            self.assertTrue(is_down)

    def test_download_bulk_returns_consistent_tuple(self):
        downloader = FacebookDownloader(self.config)
        test_file = Path(self.test_dir) / "fb_urls.txt"
        test_file.write_text("https://www.facebook.com/watch/?v=111\n", encoding="utf-8")
        
        with patch.object(downloader, "download", return_value=(True, "OK")):
            successful, failed, skipped, failed_urls = downloader.download_bulk(str(test_file))
            self.assertEqual(successful, 1)
            self.assertEqual(failed, 0)
            self.assertEqual(skipped, 0)
            self.assertEqual(failed_urls, [])

    def test_extract_video_id_patterns(self):
        downloader = FacebookDownloader(self.config)
        self.assertEqual(downloader._extract_video_id("https://facebook.com/videos/998877/"), "998877")
        self.assertEqual(downloader._extract_video_id("https://facebook.com/reel/554433"), "554433")
        self.assertIsNone(downloader._extract_video_id("https://facebook.com/unknown"))

    def test_validate_facebook_cookies_valid(self):
        downloader = FacebookDownloader(self.config)
        cookie_file = Path(self.test_dir) / "fb_cookies.txt"
        cookie_file.write_text("c_user=12345; xs=abcdef;", encoding="utf-8")
        valid, msg = downloader.validate_facebook_cookies(str(cookie_file))
        self.assertTrue(valid)
        self.assertEqual(self.config.facebook_cookies_file, str(cookie_file))

    def test_validate_facebook_cookies_invalid(self):
        downloader = FacebookDownloader(self.config)
        cookie_file = Path(self.test_dir) / "invalid_fb.txt"
        cookie_file.write_text("other_cookie=value;", encoding="utf-8")
        valid, msg = downloader.validate_facebook_cookies(str(cookie_file))
        self.assertFalse(valid)
        self.assertIn("Geçersiz", msg)

    def test_validate_facebook_cookies_missing(self):
        downloader = FacebookDownloader(self.config)
        valid, msg = downloader.validate_facebook_cookies("missing_file.txt")
        self.assertFalse(valid)
        self.assertIn("bulunamadı", msg)

    def test_close_selenium(self):
        downloader = FacebookDownloader(self.config)
        mock_driver = MagicMock()
        downloader.driver = mock_driver
        downloader.close_selenium()
        mock_driver.quit.assert_called_once()
        self.assertIsNone(downloader.driver)


class TestInterface(unittest.TestCase):
    """Tests for UI Interface methods."""

    def setUp(self):
        self.ui = Interface()

    def test_breadcrumbs(self):
        self.ui.clear_breadcrumb()
        self.assertEqual(len(self.ui.breadcrumb), 0)
        self.ui.push_breadcrumb("Home")
        self.ui.push_breadcrumb("YouTube")
        self.assertEqual(self.ui._get_breadcrumb_text(), "Home › YouTube")
        self.ui.pop_breadcrumb()
        self.assertEqual(self.ui._get_breadcrumb_text(), "Home")

    def test_theme_update(self):
        self.ui.update_theme("fedora")
        self.assertIn("primary", self.ui.colors)
        self.ui.update_theme("macintosh")
        self.assertIn("primary", self.ui.colors)

    def test_feedback_methods(self):
        with patch.object(self.ui.console, "print") as mock_print:
            self.ui.show_error("Test error")
            self.ui.show_warning("Test warning")
            self.ui.show_info("Test info")
            self.ui.show_success("Test success")
            self.assertGreaterEqual(mock_print.call_count, 4)




class TestBaseController(unittest.TestCase):
    """Tests for BaseController static helper methods."""

    def test_get_resource_path_dev(self):
        p = BaseController.get_resource_path("scripts/universal_video_collector.user.js")
        self.assertTrue(str(p).endswith("universal_video_collector.user.js"))

    def test_get_resource_path_pyinstaller(self):
        mock_meipass = str(Path(tempfile.gettempdir()) / "mock_meipass")
        with patch.object(sys, "_MEIPASS", mock_meipass, create=True):
            p = BaseController.get_resource_path("scripts/test.js")
            expected = Path(mock_meipass) / "scripts/test.js"
            self.assertEqual(p, expected)



if __name__ == "__main__":
    unittest.main()
