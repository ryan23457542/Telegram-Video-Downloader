import sys
import time
import threading
from typing import Optional

from utils.ansi import ANSI
from utils.text import visible_width, pad_right


class Box:
    """Reusable bordered box renderer so every screen (menu, login,
    download dashboard) shares one consistent, correctly-aligned style."""

    def __init__(self, width: int = 46, color: str = ANSI.BRIGHT_CYAN):
        self.width = width
        self.color = color

    def top(self) -> str:
        return f"{self.color}╔{'═' * (self.width - 2)}╗{ANSI.RESET}"

    def bottom(self) -> str:
        return f"{self.color}╚{'═' * (self.width - 2)}╝{ANSI.RESET}"

    def divider(self) -> str:
        return f"{self.color}╠{'═' * (self.width - 2)}╣{ANSI.RESET}"

    def line(self, content: str = "") -> str:
        inner_width = self.width - 2
        body = pad_right(f" {content}", inner_width)
        return f"{self.color}║{ANSI.RESET}{body}{self.color}║{ANSI.RESET}"

    def row(self, label: str, value: str, value_color: str = ANSI.BRIGHT_WHITE, label_width: int = 9) -> str:
        content = f"{ANSI.BOLD}{label:<{label_width}}{ANSI.RESET}: {value_color}{value}{ANSI.RESET}"
        return self.line(content)


class Spinner:
    """Small animated spinner shown during blocking calls (status checks,
    link resolving) so the app never appears frozen. Use as a context
    manager: `with Spinner("Checking status..."):  ...blocking call...`"""

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message: str, color: str = ANSI.BRIGHT_CYAN):
        self.message = message
        self.color = color
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _spin(self):
        idx = 0
        while not self._stop_event.is_set():
            frame = self.FRAMES[idx % len(self.FRAMES)]
            sys.stdout.write(f"\r{self.color}{frame}{ANSI.RESET} {self.message}")
            sys.stdout.flush()
            idx += 1
            self._stop_event.wait(0.08)
        # Clear the spinner line when done
        sys.stdout.write("\r" + " " * (visible_width(self.message) + 4) + "\r")
        sys.stdout.flush()

    def __enter__(self):
        sys.stdout.write(ANSI.HIDE_CURSOR)
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        sys.stdout.write(ANSI.SHOW_CURSOR)
        sys.stdout.flush()
        return False


def typewriter(text: str, delay: float = 0.015):
    """Print text with a simple typewriter reveal animation."""
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")
