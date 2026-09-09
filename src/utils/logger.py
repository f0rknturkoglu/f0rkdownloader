"""
Centralized Logging Module
Provides application-wide logging with file output and structured messages.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path


class AppLogger:
    """
    Application logger with file output and specialized logging methods.
    
    Implements singleton pattern to ensure consistent logging across the app.
    """
    
    _instance: 'AppLogger | None' = None
    
    def __new__(cls) -> 'AppLogger':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.logger = logging.getLogger("f0rkdownloader")
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Create logs directory
        self.log_dir = Path.home() / "Downloads" / "f0rkn_d0wnl0ader" / ".logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Log file path with date
        log_file = self.log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        
        # Clean old logs on startup
        self._cleanup_old_logs()
    
    def _cleanup_old_logs(self, days: int = 7) -> None:
        """Remove log files older than specified days."""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            for log_file in self.log_dir.glob("app_*.log"):
                try:
                    # Parse date from filename
                    date_str = log_file.stem.split("_")[1]
                    file_date = datetime.strptime(date_str, "%Y%m%d")
                    if file_date < cutoff:
                        log_file.unlink()
                except (ValueError, IndexError, OSError):
                    continue
        except OSError:
            pass
    
    # ==================== Standard Logging Methods ====================
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log critical message."""
        self.logger.critical(message)
    
    def exception(self, message: str, exc: Exception | None = None) -> None:
        """Log exception with traceback."""
        if exc:
            self.logger.exception(f"{message}: {exc}")
        else:
            self.logger.exception(message)
    
    # ==================== Specialized Logging Methods ====================
    
    def download_start(self, platform: str, url: str) -> None:
        """Log download start event."""
        self.logger.info(f"DOWNLOAD_START | platform={platform} | url={url[:100]}")
    
    def download_success(self, platform: str, url: str) -> None:
        """Log successful download."""
        self.logger.info(f"DOWNLOAD_SUCCESS | platform={platform} | url={url[:100]}")
    
    def download_fail(self, platform: str, url: str, error: str) -> None:
        """Log failed download."""
        self.logger.error(
            f"DOWNLOAD_FAIL | platform={platform} | url={url[:100]} | error={error[:200]}"
        )
    
    def auth_event(self, platform: str, success: bool, method: str) -> None:
        """Log authentication event."""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"AUTH_{status} | platform={platform} | method={method}")


# ==================== Module-level Functions ====================

_logger_instance: AppLogger | None = None


def get_logger() -> AppLogger:
    """
    Get the singleton logger instance.
    
    Returns:
        AppLogger: The application logger
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AppLogger()
    return _logger_instance


def cleanup_logs(days: int = 7) -> None:
    """
    Manually trigger log cleanup.
    
    Args:
        days: Remove logs older than this many days
    """
    logger = get_logger()
    logger._cleanup_old_logs(days)
