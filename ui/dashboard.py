import sys
import time
import re
from dataclasses import dataclass
from typing import Optional
from utils.ansi import ANSI
from utils.helpers import format_bytes, format_time, get_terminal_width
from utils.ping import NetworkState
from core.resolver import DownloadProfile

@dataclass
class DownloadProgress:
    transferred_bytes: int = 0
    total_bytes: int = 0
    percentage: float = 0.0
    speed_bytes_sec: float = 0.0
    eta_seconds: float = 0.0
    status_text: str = "Initializing..."

class LiveDashboard:
    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, file_name: str, size_bytes: Optional[int], profile: DownloadProfile):
        self.file_name = file_name
        self.size_bytes = size_bytes or 0
        self.profile = profile
        self.start_time = time.time()
        self.spinner_idx = 0

    def render(self, progress: DownloadProgress, net_state: NetworkState):
        term_width = max(get_terminal_width(), 60)
        box_width = min(term_width - 4, 68)

        self.spinner_idx = (self.spinner_idx + 1) % len(self.SPINNER_FRAMES)
        spinner = f"{ANSI.BRIGHT_CYAN}{self.SPINNER_FRAMES[self.spinner_idx]}{ANSI.RESET}"

        elapsed_str = format_time(time.time() - self.start_time)
        speed_str = f"{format_bytes(progress.speed_bytes_sec)}/s"
        transferred_str = format_bytes(progress.transferred_bytes)
        total_str = format_bytes(self.size_bytes) if self.size_bytes > 0 else "Unknown"

        lines = [
            f"{ANSI.MOVE_HOME}{ANSI.BRIGHT_CYAN}╔{'═' * (box_width - 2)}╗{ANSI.RESET}",
            f"{ANSI.BRIGHT_CYAN}║{ANSI.RESET} {ANSI.BOLD}{ANSI.BRIGHT_MAGENTA}🚀 TELEGRAM DOWNLOADER v7{ANSI.RESET}{' ' * (box_width - 27)}{ANSI.BRIGHT_CYAN}║{ANSI.RESET}",
            f"{ANSI.BRIGHT_CYAN}╠{'═' * (box_width - 2)}╣{ANSI.RESET}",
            self._format_row("File", self.file_name, ANSI.BRIGHT_GREEN, box_width),
            self._format_row("Size", total_str, ANSI.BRIGHT_YELLOW, box_width),
            self._format_row("Speed", speed_str, ANSI.BRIGHT_GREEN, box_width),
            self._format_row("Progress", f"{transferred_str} ({progress.percentage:.1f}%)", ANSI.BRIGHT_WHITE, box_width),
            self._format_row("Status", f"{spinner} {progress.status_text}", ANSI.BRIGHT_WHITE, box_width),
            f"{ANSI.BRIGHT_CYAN}╚{'═' * (box_width - 2)}╝{ANSI.RESET}"
        ]

        output = "\n".join(ANSI.clear_line() + line for line in lines)
        sys.stdout.write(output)
        sys.stdout.flush()

    def _format_row(self, label: str, value: str, val_color: str, box_width: int) -> str:
        left_str = f"  {ANSI.BOLD}{label:<10}{ANSI.RESET}: {val_color}{value}{ANSI.RESET}"
        plain_left = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', left_str)
        padding = max(0, box_width - len(plain_left) - 2)
        return f"{ANSI.BRIGHT_CYAN}║{ANSI.RESET}{left_str}{' ' * padding}{ANSI.BRIGHT_CYAN}║{ANSI.RESET}"
  
