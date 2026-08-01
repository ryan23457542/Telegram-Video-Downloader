from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class DownloadProfile:
    name: str
    threads: int
    pool: int

class MetadataResolver:
    @staticmethod
    def parse_link(link: str, namespace: str, proxy: str = "") -> Tuple[Optional[int], str]:
        """
        Current tdl builds have no subcommand for resolving a single
        message link's size/name up front (checked against the shipped
        `tdl` binary: only backup, chat, download/dl, extension, forward,
        login, migrate, recover, upload, version exist - there is no
        `url`/`url parse`). That command this used to call no longer
        exists, so it always failed silently and every download fell
        back to "Telegram_Media" / Unknown size / Balanced Mode.

        There's no supported way to get this metadata without starting
        the download, so we return the fallback here and let
        DownloadEngine back-fill the real size once tdl's own progress
        output reports the first downloaded chunk (see
        DownloadEngine._update_progress).
        """
        return None, "Telegram_Media"

    @staticmethod
    def select_profile(size_bytes: Optional[int]) -> DownloadProfile:
        if not size_bytes or size_bytes <= 0:
            return DownloadProfile("Balanced Mode", 8, 8)
        size_mb = size_bytes / (1024 * 1024)
        if size_mb < 25: return DownloadProfile("Low Overhead Mode", 4, 4)
        elif size_mb < 250: return DownloadProfile("High-Speed Mode", 8, 8)
        elif size_mb < 1024: return DownloadProfile("Turbo Extreme Mode", 16, 16)
        return DownloadProfile("Ultra Large File Engine", 24, 24)

        
