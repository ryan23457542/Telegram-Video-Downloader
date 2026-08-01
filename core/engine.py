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
from utils.helpers import force_unlock_tdl_database

class DownloadEngine:
    def __init__(self, link: str, config: AppConfig):
        # ... သင်၏ init code များ ...
        pass

    def execute(self) -> bool:
        # Download မစခင် Process နဲ့ Lock file ရှင်းမည်
        force_unlock_tdl_database()
        
        # ... ကျန်ရှိသော download execution code များ ...


class DownloadEngine:
    def __init__(self, link: str, config: AppConfig):
        self.link = link
        self.config = config
        self.stop_event = threading.Event()
        self.progress = DownloadProgress()
        self.lock = threading.Lock()
        
        self.size_bytes, self.file_name = MetadataResolver.parse_link(link, config.namespace)
        self.profile = MetadataResolver.select_profile(self.size_bytes)
        
        self.ping_monitor = PingMonitor()
        self.dashboard = LiveDashboard(self.file_name, self.size_bytes, self.profile)

    def execute(self) -> bool:
        self.ping_monitor.start()
        cmd = [
            "tdl", "-n", self.config.namespace, "dl", "-u", self.link,
            "-t", str(self.profile.threads), "--pool", str(self.profile.pool),
            "-d", self.config.download_dir, "--reconnect-timeout", "15s"
        ]

        sys.stdout.write(ANSI.CLEAR_SCREEN + ANSI.HIDE_CURSOR)
        sys.stdout.flush()

        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            threading.Thread(target=self._parse_output, args=(process,), daemon=True).start()

            while process.poll() is None:
                if self.stop_event.is_set():
                    process.terminate()
                    break
                self.dashboard.render(self.progress, self.ping_monitor.get_state())
                time.sleep(0.12)

            ret_code = process.wait()
            self.ping_monitor.stop()

            if ret_code == 0 and not self.stop_event.is_set():
                self.progress.percentage = 100.0
                self.progress.status_text = "Completed!"
                self.dashboard.render(self.progress, self.ping_monitor.get_state())
                return True
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
        if pct_match:
            with self.lock:
                self.progress.percentage = float(pct_match.group(1))
                self.progress.status_text = "Downloading..."
