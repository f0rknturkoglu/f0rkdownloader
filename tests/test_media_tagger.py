"""
Tests for Media Tagger and ID3 Metadata enrichment.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.utils.media_tagger import enrich_mp3_metadata


class TestMediaTagger(unittest.TestCase):
    """Unit tests for media tagger."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_non_existent_file(self):
        result = enrich_mp3_metadata("non_existent_file.mp3", title="Test")
        self.assertFalse(result)

    def test_invalid_extension(self):
        txt_file = Path(self.test_dir) / "test.txt"
        txt_file.write_text("not an mp3", encoding="utf-8")
        result = enrich_mp3_metadata(str(txt_file), title="Test")
        self.assertFalse(result)

    @patch("src.utils.media_tagger.ID3")
    def test_enrich_mp3_metadata_success(self, mock_id3_cls):
        mock_id3_instance = MagicMock()
        mock_id3_cls.return_value = mock_id3_instance

        # Create dummy mp3 file
        mp3_file = Path(self.test_dir) / "sample.mp3"
        mp3_file.write_bytes(b"\xff\xfb\x90\x00" + b"\x00" * 200)

        # Create dummy cover art
        cover_file = Path(self.test_dir) / "cover.jpg"
        cover_file.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 50)

        success = enrich_mp3_metadata(
            mp3_file,
            title="Sample Track",
            artist="Sample Artist",
            album="Sample Album",
            cover_image_path=cover_file,
        )

        self.assertTrue(success)
        mock_id3_instance.save.assert_called_once()


if __name__ == "__main__":
    unittest.main()
