"""
Tests for the Logger module.
"""

# Add src to path
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestLogger(unittest.TestCase):
    """Test cases for AppLogger class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        
        # Reset the singleton for each test
        import src.utils.logger as logger_module
        logger_module._logger_instance = None
        if hasattr(logger_module.AppLogger, '_instance'):
            logger_module.AppLogger._instance = None
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        # Reset singleton
        import src.utils.logger as logger_module
        logger_module._logger_instance = None
        if hasattr(logger_module.AppLogger, '_instance'):
            logger_module.AppLogger._instance = None
    
    def test_logger_singleton(self):
        """Test that logger is a singleton."""
        from src.utils.logger import get_logger
        
        logger1 = get_logger()
        logger2 = get_logger()
        
        self.assertIs(logger1, logger2)
    
    def test_log_methods_dont_raise(self):
        """Test that log methods don't raise exceptions."""
        from src.utils.logger import get_logger
        
        logger = get_logger()
        
        # These should not raise exceptions
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
    
    def test_download_logging(self):
        """Test download-specific logging methods."""
        from src.utils.logger import get_logger
        
        logger = get_logger()
        
        # These should not raise exceptions
        logger.download_start("youtube", "https://youtube.com/test")
        logger.download_success("youtube", "https://youtube.com/test")
        logger.download_fail("youtube", "https://youtube.com/test", "Test error")
    
    def test_auth_logging(self):
        """Test authentication logging methods."""
        from src.utils.logger import get_logger
        
        logger = get_logger()
        
        # These should not raise exceptions
        logger.auth_event("twitter", True, "cookie_file")
        logger.auth_event("youtube", False, "browser")
    
    def test_exception_logging(self):
        """Test exception logging."""
        from src.utils.logger import get_logger
        
        logger = get_logger()
        
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            # Should not raise
            logger.exception("Test exception occurred", exc=e)


if __name__ == "__main__":
    unittest.main()
