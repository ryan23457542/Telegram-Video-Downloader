import re
import subprocess
import threading
from dataclasses import dataclass
from typing import Optional
from utils.ansi import ANSI

@dataclass
class NetworkState:
    ping_ms: float = -1.0
    quality_label: str = "🔴 Offline"
    quality_color: str = ANSI.RED

class PingMonitor:
    def __init__(self, target_host: str = "91.108.56.191"):
        self.target_host = target_host
        self.state = NetworkState()
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread: Optional[threading.Thread] = None

    def start(self):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

    def get_state(self) -> NetworkState:
        with self.lock:
            return NetworkState(self.state.ping_ms, self.state.quality_label, self.state.quality_color)

    def _run(self):
        samples = []
        cmd = ["ping", "-c", "1", "-W", "2", self.target_host]
        while not self.stop_event.is_set():
            ping_val = self._single_ping(cmd)
            if ping_val is not None:
                samples.append(ping_val)
                if len(samples) > 3: samples.pop(0)
                avg_ping = sum(samples) / len(samples)
                
                if avg_ping < 90: label, color = "🟢 Excellent", ANSI.BRIGHT_GREEN
                elif avg_ping < 200: label, color = "🟡 Good", ANSI.BRIGHT_YELLOW
                else: label, color = "🟠 Slow", ANSI.YELLOW
            else:
                samples.clear()
                avg_ping, label, color = -1.0, "🔴 Offline", ANSI.BRIGHT_RED

            with self.lock:
                self.state.ping_ms, self.state.quality_label, self.state.quality_color = avg_ping, label, color

            self.stop_event.wait(3.0)

    def _single_ping(self, cmd: list) -> Optional[float]:
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            if proc.returncode == 0:
                match = re.search(r"time=([\d\.]+)\s*ms", proc.stdout)
                if match: return float(match.group(1))
        except Exception:
            pass
        return None
