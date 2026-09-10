"""
Channel and Profile Watcher Module
Monitors followed channels or profiles for new video uploads and archives them automatically.
"""

import json
from pathlib import Path
from typing import Any
import yt_dlp


class ChannelWatcher:
    """Manages watched channels/profiles and discovers new uploads."""

    def __init__(self, base_path: Path):
        self.storage_file = base_path / "watched_channels.json"
        self._targets: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if self.storage_file.exists():
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    self._targets = json.load(f)
            except Exception:
                self._targets = []

    def _save(self) -> None:
        try:
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(self._targets, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def add_target(self, url: str, platform: str, name: str = "") -> dict[str, Any]:
        """Add a new channel or profile to watch list."""
        clean_url = url.strip()
        target = {
            "id": f"{platform}_{len(self._targets) + 1}",
            "url": clean_url,
            "platform": platform,
            "name": name or clean_url,
            "last_checked": None,
            "known_videos": [],
        }
        self._targets.append(target)
        self._save()
        return target

    def remove_target(self, target_id: str) -> bool:
        """Remove a target from watch list."""
        initial_len = len(self._targets)
        self._targets = [t for t in self._targets if t.get("id") != target_id]
        if len(self._targets) != initial_len:
            self._save()
            return True
        return False

    def list_targets(self) -> list[dict[str, Any]]:
        """List all currently watched channels/profiles."""
        return list(self._targets)

    def scan_target_for_new_videos(self, target: dict[str, Any], limit: int = 5) -> list[str]:
        """
        Scan a channel or profile for new videos.
        Returns newly discovered video URLs that haven't been downloaded yet.
        """
        url = target.get("url")
        if not url:
            return []

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "playlistend": limit,
            "js_runtimes": {
                "node": {},
                "deno": {},
                "bun": {},
                "quickjs": {},
            },
        }

        discovered_urls: list[str] = []
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return []

                entries = info.get("entries", [])
                known = set(target.get("known_videos", []))

                new_entries = []
                for entry in entries:
                    if not entry:
                        continue
                    v_url = entry.get("url") or entry.get("webpage_url")
                    if v_url and v_url not in known:
                        discovered_urls.append(v_url)
                        new_entries.append(v_url)

                if new_entries:
                    target["known_videos"] = list(known.union(new_entries))
                    self._save()
        except Exception:
            pass

        return discovered_urls
