import sys
import time
from dataclasses import dataclass
from typing import Optional

from utils.ansi import ANSI
from utils.helpers import format_bytes, format_time, get_terminal_width
from utils.text import pad_right, truncate
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
    last_line: str = ""


class LiveDashboard:
    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    BAR_FILLED = "█"
    BAR_EMPTY = "░"

    def __init__(self, file_name: str, size_bytes: Optional[int], profile: DownloadProfile):
        self.file_name = file_name
        self.size_bytes = size_bytes or 0
        self.profile = profile
        self.start_time = time.time()
        self.spinner_idx = 0

    def render(self, progress: DownloadProgress, net_state: NetworkState):
        term_width = max(get_terminal_width(), 60)
        box_width = min(term_width - 4, 68)
        inner_width = box_width - 2

        self.spinner_idx = (self.spinner_idx + 1) % len(self.SPINNER_FRAMES)
        spinner = f"{ANSI.BRIGHT_CYAN}{self.SPINNER_FRAMES[self.spinner_idx]}{ANSI.RESET}"

        speed_str = f"{format_bytes(progress.speed_bytes_sec)}/s"
        transferred_str = format_bytes(progress.transferred_bytes)
        total_str = format_bytes(self.size_bytes) if self.size_bytes > 0 else "Unknown"
        eta_str = format_time(progress.eta_seconds)
        ping_str = f"{net_state.ping_ms:.0f} ms" if net_state.ping_ms >= 0 else "--"

        title = "🚀 TELEGRAM DOWNLOADER v7"
        title_line = pad_right(f" {ANSI.BOLD}{ANSI.BRIGHT_MAGENTA}{title}{ANSI.RESET}", inner_width)

        lines = [
            f"{ANSI.BRIGHT_CYAN}╔{'═' * (box_width - 2)}╗{ANSI.RESET}",
            f"{ANSI.BRIGHT_CYAN}║{ANSI.RESET}{title_line}{ANSI.BRIGHT_CYAN}║{ANSI.RESET}",
            f"{ANSI.BRIGHT_CYAN}╠{'═' * (box_width - 2)}╣{ANSI.RESET}",
            self._format_row("File", self.file_name, ANSI.BRIGHT_GREEN, box_width),
            self._format_row("Size", total_str, ANSI.BRIGHT_YELLOW, box_width),
            self._format_row("Speed", speed_str, ANSI.BRIGHT_GREEN, box_width),
            self._format_row("ETA", eta_str, ANSI.BRIGHT_WHITE, box_width),
            self._format_row("Network", f"{net_state.quality_label} ({ping_str})", net_state.quality_color, box_width),
            self._format_bar_row(progress.percentage, box_width),
            self._format_row("Progress", f"{transferred_str} / {total_str} ({progress.percentage:.1f}%)", ANSI.BRIGHT_WHITE, box_width),
            self._format_row("Status", f"{spinner} {progress.status_text}", ANSI.BRIGHT_WHITE, box_width),
            self._format_row("tdl says", truncate(progress.last_line or "(no output yet)", max(10, inner_width - 14)), ANSI.DIM, box_width),
            f"{ANSI.BRIGHT_CYAN}╚{'═' * (box_width - 2)}╝{ANSI.RESET}",
        ]

        # Move cursor to the top of our block and repaint every line, clearing
        # any leftover characters from a previous, wider render.
        sys.stdout.write(ANSI.MOVE_HOME)
        sys.stdout.write("\n".join(ANSI.clear_line() + line for line in lines))
        sys.stdout.write("\n")
        sys.stdout.flush()

    def _format_row(self, label: str, value: str, val_color: str, box_width: int) -> str:
        inner_width = box_width - 2
        left_str = f"  {ANSI.BOLD}{label:<10}{ANSI.RESET}: {val_color}{value}{ANSI.RESET}"
        body = pad_right(left_str, inner_width)
        return f"{ANSI.BRIGHT_CYAN}║{ANSI.RESET}{body}{ANSI.BRIGHT_CYAN}║{ANSI.RESET}"

    def _format_bar_row(self, percentage: float, box_width: int) -> str:
        inner_width = box_width - 2
        pct = max(0.0, min(100.0, percentage))
        bar_width = max(10, inner_width - 12)
        filled = int(bar_width * pct / 100)
        bar = f"{ANSI.BRIGHT_GREEN}{self.BAR_FILLED * filled}{ANSI.DIM}{self.BAR_EMPTY * (bar_width - filled)}{ANSI.RESET}"
        content = f"  [{bar}] {pct:5.1f}%"
        body = pad_right(content, inner_width)
        return f"{ANSI.BRIGHT_CYAN}║{ANSI.RESET}{body}{ANSI.BRIGHT_CYAN}║{ANSI.RESET}"
                      
