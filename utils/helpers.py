import os
import socket
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse
from utils.text import strip_ansi

def format_bytes(size: float) -> str:
    """Format bytes into human readable format."""
    if size <= 0:
        return "0.00 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def format_time(seconds: float) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if seconds <= 0 or seconds > 864000:
        return "--:--"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

def get_terminal_width(default: int = 60) -> int:
    """Get terminal width dynamically."""
    return shutil.get_terminal_size((default, 24)).columns

def check_tdl_installed() -> bool:
    """Check if 'tdl' command is available in PATH."""
    return shutil.which("tdl") is not None

def force_unlock_tdl_database():
    """TDL process အားလုံးကို သတ်ပြီး ကျန်ခဲ့သော Lock File များကို ရှင်းထုတ်ပေးမည်"""
    try:
        # 1. Background က tdl process မှန်သမျှ အကုန်သတ်မည်
        subprocess.run(["pkill", "-9", "tdl"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        time.sleep(0.3)

        # 2. tdl ရဲ့ lock file များ ကျန်ခဲ့ပါက အတင်းဖျက်မည်
        tdl_dir = Path.home() / ".tdl"
        if tdl_dir.exists():
            for lock_file in tdl_dir.glob("*.lock"):
                try:
                    os.remove(lock_file)
                except Exception:
                    pass
    except Exception:
        pass


def test_proxy_reachable(proxy: str, timeout: float = 4.0):
    """
    Quickly test whether a proxy's host:port accepts a raw TCP connection.
    This does NOT verify the proxy actually forwards traffic correctly
    (that needs a real SOCKS/HTTP handshake), but it catches the most
    common failure - a dead/offline proxy - in a few seconds instead of
    letting tdl hang on it for a minute or more with no feedback.
    Returns (is_reachable, detail_message).
    """
    if not proxy:
        return True, ""
    try:
        parsed = urlparse(proxy)
        host, port = parsed.hostname, parsed.port
        if not host or not port:
            return False, "Could not parse host/port from proxy address"
        with socket.create_connection((host, port), timeout=timeout):
            return True, ""
    except Exception as e:
        return False, str(e)


def last_meaningful_line(text: str, max_len: int = 80) -> str:
    """
    Pull the last non-empty, non-noise line out of tdl's raw stdout/stderr
    so failures can show the *real* reason tdl gave instead of a guessed
    generic label like "Connection lost" or "Not Logged In". Without this,
    every failure - a bad namespace, a private/inaccessible chat, an auth
    error, an actual network drop, anything - looked identical to the user.
    """
    if not text:
        return ""
    noise_prefixes = ("cpu:", "memory:", "goroutines:")
    for raw_line in reversed(text.splitlines()):
        line = strip_ansi(raw_line).strip()
        if not line or line.lower().startswith(noise_prefixes):
            continue
        return line[:max_len] + ("…" if len(line) > max_len else "")
    return ""

    
