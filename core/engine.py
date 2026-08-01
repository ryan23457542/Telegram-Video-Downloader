import sys
import re
import time
import subprocess
import threading
from utils.ansi import ANSI
from utils.ping import PingMonitor
from config import AppConfig
from core.resolver import MetadataResolver
from ui.dashboard import LiveDashboard, DownloadProgress
from utils.helpers import force_unlock_tdl_database, test_proxy_reachable
from ui.box import Spinner


class DownloadEngine:
    def __init__(self, link: str, config: AppConfig):
        self.link = link
        self.config = config
        self.stop_event = threading.Event()
        self.progress = DownloadProgress()
        self.lock = threading.Lock()

        # Stale locks from a previous crashed/killed run would silently
        # block every new download - clear them before we touch tdl at all.
        force_unlock_tdl_database()

        if config.proxy:
            reachable, detail = test_proxy_reachable(config.proxy, timeout=5.0)
            if not reachable:
                raise RuntimeError(f"Proxy '{config.proxy}' is unreachable ({detail}). Try a different proxy.")

        with Spinner("Resolving link metadata..."):
            self.size_bytes, self.file_name = MetadataResolver.parse_link(link, config.namespace, config.proxy)
        self.profile = MetadataResolver.select_profile(self.size_bytes)

        self.ping_monitor = PingMonitor()
        self.dashboard = LiveDashboard(self.file_name, self.size_bytes, self.profile)
        self._last_sample_time: float = 0.0
        self._last_sample_bytes: float = 0.0

    def execute(self) -> bool:
        self.ping_monitor.start()
        cmd = [
            "tdl", "-n", self.config.namespace, "dl", "-u", self.link,
            "-t", str(self.profile.threads), "--pool", str(self.profile.pool),
            "-d", self.config.download_dir, "--reconnect-timeout", "15s"
        ]
        if self.config.proxy:
            cmd += ["--proxy", self.config.proxy]

        sys.stdout.write(ANSI.CLEAR_SCREEN + ANSI.HIDE_CURSOR)
        sys.stdout.flush()

        process = None
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            threading.Thread(target=self._parse_output, args=(process,), daemon=True).start()

            while process.poll() is None:
                if self.stop_event.is_set():
                    break
                self.dashboard.render(self.progress, self.ping_monitor.get_state())
                time.sleep(0.12)

            if self.stop_event.is_set() and process.poll() is None:
                process.terminate()

            ret_code = process.wait()
            self.ping_monitor.stop()

            if ret_code == 0 and not self.stop_event.is_set():
                self.progress.percentage = 100.0
                self.progress.status_text = "Completed!"
                self.dashboard.render(self.progress, self.ping_monitor.get_state())
                return True
            if self.stop_event.is_set():
                self.progress.status_text = "Cancelled"
            return False
        except KeyboardInterrupt:
            # Don't leave an orphaned tdl process running in the background
            self.stop_event.set()
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
            self.ping_monitor.stop()
            return False
        finally:
            sys.stdout.write(ANSI.SHOW_CURSOR + "\n")

    def _parse_output(self, process: subprocess.Popen):
        if not process.stdout: return
        buffer = ""
        while not self.stop_event.is_set():
            char = process.stdout.read(1)
            if not char: break
            if char in ('\r', '\n'):
                if buffer.strip(): self._update_progress(buffer.strip())
                buffer = ""
            else: buffer += char

    def _update_progress(self, line: str):
        pct_match = re.search(r"([\d\.]+)%", line)
        if not pct_match:
            return
        pct = min(100.0, max(0.0, float(pct_match.group(1))))

        # tdl's progress line often looks like:
        # "45.5% [140.00 MB in 5m14s; ETA: 42m26s; 455.5 KB/s]"
        # Prefer these explicit fields when present - they're exact,
        # not estimated from timing between our own polls.
        size_match = re.search(r"\[([\d\.]+)\s*([KMGT]?B)\b", line)
        speed_match = re.search(r"([\d\.]+)\s*([KMGT]?B)/s", line)
        eta_match = re.search(r"ETA:\s*([\dhms]+)", line)

        now = time.time()
        with self.lock:
            self.progress.percentage = pct
            self.progress.status_text = "Downloading..."

            if size_match:
                self.progress.transferred_bytes = self._to_bytes(float(size_match.group(1)), size_match.group(2))
            elif self.size_bytes:
                self.progress.transferred_bytes = (pct / 100.0) * self.size_bytes

            if speed_match:
                self.progress.speed_bytes_sec = self._to_bytes(float(speed_match.group(1)), speed_match.group(2))
            elif self._last_sample_time > 0:
                dt = now - self._last_sample_time
                if dt >= 0.2:
                    speed = (self.progress.transferred_bytes - self._last_sample_bytes) / dt
                    if speed >= 0:
                        self.progress.speed_bytes_sec = speed

            if eta_match:
                self.progress.eta_seconds = self._parse_eta(eta_match.group(1))
            elif self.progress.speed_bytes_sec > 0 and self.size_bytes:
                remaining = max(0.0, self.size_bytes - self.progress.transferred_bytes)
                self.progress.eta_seconds = remaining / self.progress.speed_bytes_sec
            else:
                self.progress.eta_seconds = 0.0

            self._last_sample_time = now
            self._last_sample_bytes = self.progress.transferred_bytes

    @staticmethod
    def _to_bytes(value: float, unit: str) -> float:
        units = {"B": 1, "KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3, "TB": 1024 ** 4}
        return value * units.get(unit.upper(), 1)

    @staticmethod
    def _parse_eta(eta_str: str) -> float:
        total = 0.0
        h = re.search(r"(\d+)h", eta_str)
        m = re.search(r"(\d+)m", eta_str)
        s = re.search(r"(\d+)s", eta_str)
        if h: total += int(h.group(1)) * 3600
        if m: total += int(m.group(1)) * 60
        if s: total += int(s.group(1))
        return total
