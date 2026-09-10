"""
Media Tagger Utility
Enriches audio files (MP3) with ID3 tags and embedded album art cover using mutagen.
"""

from pathlib import Path
from typing import Any

from mutagen.id3 import APIC, ID3, TALB, TIT2, TPE1, ID3NoHeaderError


def enrich_mp3_metadata(
    mp3_path: str | Path,
    title: str | None = None,
    artist: str | None = None,
    album: str | None = None,
    cover_image_path: str | Path | None = None,
) -> bool:
    """
    Enrich an MP3 file with ID3 tags and embed an album cover image.

    Args:
        mp3_path: Path to the target MP3 file.
        title: Track title.
        artist: Artist/channel name.
        album: Album name.
        cover_image_path: Path to image file (jpg/png) to embed as album art.

    Returns:
        bool: True if metadata/cover was embedded successfully.
    """
    try:
        path = Path(mp3_path)
        if not path.exists() or path.suffix.lower() != ".mp3":
            return False

        try:
            audio = ID3(str(path))
        except ID3NoHeaderError:
            audio = ID3()

        if title:
            audio.add(TIT2(encoding=3, text=title))
        if artist:
            audio.add(TPE1(encoding=3, text=artist))
        if album:
            audio.add(TALB(encoding=3, text=album))

        if cover_image_path:
            cover_path = Path(cover_image_path)
            if cover_path.exists():
                mime = "image/jpeg" if cover_path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
                with open(cover_path, "rb") as img:
                    audio.add(
                        APIC(
                            encoding=3,
                            mime=mime,
                            type=3,  # Cover (front)
                            desc="Cover",
                            data=img.read(),
                        )
                    )

        audio.save(str(path))
        return True
    except Exception:
        return False
