"""
Main Entry Point
f0rkn_d0wnl0ader v3.0
A clean, modular downloader with multi-platform support, Textual TUI, and automated services.
"""

import sys
from typing import Any

from src.config import Config
from src.ui.interface import Interface
from src.utils.logger import get_logger

# Controllers
from src.controllers.account_controller import AccountController
from src.controllers.facebook_controller import FacebookController
from src.controllers.instagram_controller import InstagramController
from src.controllers.pinterest_controller import PinterestController
from src.controllers.settings_controller import SettingsController
from src.controllers.tiktok_controller import TikTokController
from src.controllers.twitter_controller import TwitterController
from src.controllers.watcher_controller import AutomationController
from src.controllers.youtube_controller import YouTubeController


class Application:
    """Main application orchestrator."""

    def __init__(self):
        # Initialize Core components
        self.config = Config()
        self.ui = Interface()
        self.logger = get_logger()

        # Initialize Platform Controllers
        self.controllers: dict[str, Any] = {
            "youtube": YouTubeController(self.config, self.ui),
            "twitter": TwitterController(self.config, self.ui),
            "tiktok": TikTokController(self.config, self.ui),
            "facebook": FacebookController(self.config, self.ui),
            "instagram": InstagramController(self.config, self.ui),
            "pinterest": PinterestController(self.config, self.ui),
            "settings": SettingsController(self.config, self.ui),
            "account": AccountController(self.config, self.ui),
        }

        # Initialize Automation Controller (has access to platform controllers)
        self.controllers["automation"] = AutomationController(
            self.config, self.ui, app_controllers=self.controllers
        )

    def run_cli(self) -> None:
        """Classic Questionary CLI loop."""
        self.logger.info("CLI loop started")

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

    def run_tui(self) -> None:
        """Modern Textual Sidebar TUI."""
        try:
            from src.ui.tui.app import F0rkDownloaderTUI
            tui_app = F0rkDownloaderTUI(config=self.config)
            tui_app.run()
        except Exception as e:
            self.logger.warning(f"TUI başlatılamadı ({e}), CLI moduna geçiliyor...")
            self.run_cli()

    def run(self) -> None:
        """Determines whether to start in TUI mode or CLI mode."""
        self.logger.info("Application started")
        if "--cli" in sys.argv or not sys.stdin.isatty():
            self.run_cli()
        else:
            self.run_tui()

    def _route(self, choice: str) -> None:
        """Route user choice to the correct controller."""
        if "YouTube" in choice:
            self.controllers["youtube"].run()
        elif "TikTok" in choice:
            self.controllers["tiktok"].run()
        elif "Twitter" in choice:
            self.controllers["twitter"].run()
        elif "Facebook" in choice:
            self.controllers["facebook"].run()
        elif "Instagram" in choice:
            self.controllers["instagram"].run()
        elif "Pinterest" in choice:
            self.controllers["pinterest"].run()
        elif "Pano İzleme" in choice:
            self.controllers["automation"].run_clipboard_menu()
        elif "Kanal ve Profil" in choice:
            self.controllers["automation"].run_channel_menu()
        elif "Tarayıcı Köprü" in choice:
            self.controllers["automation"].run_bridge_menu()
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
