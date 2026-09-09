"""
Main Entry Point
f0rkn_d0wnl0ader v2.1
A clean, modular downloader with multi-platform support.
"""

import sys
from typing import Any

from src.config import Config
from src.ui.interface import Interface
from src.utils.logger import get_logger

# Controllers
from src.controllers.youtube_controller import YouTubeController
from src.controllers.twitter_controller import TwitterController
from src.controllers.tiktok_controller import TikTokController
from src.controllers.facebook_controller import FacebookController
from src.controllers.settings_controller import SettingsController
from src.controllers.account_controller import AccountController


class Application:
    """Main application orchestrator."""

    def __init__(self):
        # Initialize Core components
        self.config = Config()
        self.ui = Interface()
        self.logger = get_logger()
        
        # Initialize Controllers (Dependency Injection)
        self.controllers: dict[str, Any] = {
            "youtube": YouTubeController(self.config, self.ui),
            "twitter": TwitterController(self.config, self.ui),
            "tiktok": TikTokController(self.config, self.ui),
            "facebook": FacebookController(self.config, self.ui),
            "settings": SettingsController(self.config, self.ui),
            "account": AccountController(self.config, self.ui),
        }

    def run(self) -> None:
        """Main application loop."""
        self.logger.info("Application started")
        
        while True:
            try:
                # Refresh UI header and theme
                self.ui.update_theme(self.config.theme_color)
                self.ui.print_header(self.config.download_path)
                
                # Main menu selection
                choice = self.ui.ask_main_menu()
                
                if not choice or "Çıkış" in choice:
                    self.shutdown()
                    break
                
                # Route to appropriate controller
                self._route(choice)
                
            except KeyboardInterrupt:
                self.shutdown()
                break
            except Exception as e:
                self.logger.exception("Unexpected error in main loop", exc=e)
                self.ui.show_error(f"Beklenmedik bir hata oluştu:\n{e}")
                self.ui.wait_for_enter()

    def _route(self, choice: str) -> None:
        """Route user choice to the correct controller."""
        if "YouTube" in choice:
            self.controllers["youtube"].run()
        elif "Twitter" in choice:
            self.controllers["twitter"].run()
        elif "TikTok" in choice:
            self.controllers["tiktok"].run()
        elif "Facebook" in choice:
            self.controllers["facebook"].run()
        elif "Ayarlar" in choice:
            self.controllers["settings"].run()
        elif "Hesap" in choice:
            self.controllers["account"].run()

    def shutdown(self) -> None:
        """Clean up and exit application."""
        self.logger.info("Application shutting down")
        fb_controller = self.controllers.get("facebook")
        if fb_controller and hasattr(fb_controller, "downloader"):
            fb_controller.downloader.close_selenium()
        self.ui.clear_screen()
        print("\n\n" + " " * 20 + "Görüşmek üzere!\n\n")
        sys.exit(0)


if __name__ == "__main__":
    app = Application()
    app.run()
