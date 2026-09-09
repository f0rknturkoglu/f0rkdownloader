"""
Unit tests for the Theme module.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui.theme import THEMES, get_colors, get_style


class TestTheme(unittest.TestCase):
    """Test suite for theme styling and colors."""

    def test_themes_definitions(self):
        """Test that all required themes exist with valid schema."""
        required_themes = ["ubuntu", "macintosh", "fedora"]
        required_keys = ["primary", "secondary", "hex", "success", "error", "warning"]

        for tname in required_themes:
            self.assertIn(tname, THEMES, f"Theme {tname} is missing in THEMES")
            theme_dict = THEMES[tname]
            for key in required_keys:
                self.assertIn(key, theme_dict, f"Key {key} is missing in theme {tname}")
                self.assertIsInstance(theme_dict[key], str)

    def test_get_style_valid_themes(self):
        """Test get_style generates a Style instance for all themes."""
        for tname in ["ubuntu", "macintosh", "fedora"]:
            style = get_style(tname)
            self.assertIsNotNone(style)

    def test_get_style_fallback(self):
        """Test get_style falls back gracefully for unknown themes."""
        style = get_style("nonexistent_theme")
        self.assertIsNotNone(style)

    def test_get_colors_valid_themes(self):
        """Test get_colors returns proper dictionary structure."""
        required_color_keys = ["primary", "secondary", "success", "error", "warning", "info", "text"]
        for tname in ["ubuntu", "macintosh", "fedora"]:
            colors = get_colors(tname)
            for key in required_color_keys:
                self.assertIn(key, colors)
            self.assertEqual(colors["primary"], THEMES[tname]["primary"])

    def test_get_colors_fallback(self):
        """Test get_colors falls back to ubuntu for unknown themes."""
        colors = get_colors("unknown_theme")
        self.assertEqual(colors["primary"], THEMES["ubuntu"]["primary"])
        self.assertEqual(colors["text"], "white")


if __name__ == "__main__":
    unittest.main()
