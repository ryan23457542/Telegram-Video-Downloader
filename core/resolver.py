import json
import subprocess
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
        cmd = ["tdl", "-n", namespace]
        if proxy:
            cmd += ["--proxy", proxy]
        cmd += ["url", "parse", "-u", link, "--json"]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=10)
            if res.returncode == 0 and res.stdout:
                data = json.loads(res.stdout)
                if isinstance(data, list) and len(data) > 0:
                    return data[0].get('size'), data[0].get('name', 'Telegram_File')
        except Exception:
            pass
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
                                 
