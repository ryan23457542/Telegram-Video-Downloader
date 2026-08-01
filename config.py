import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict

CONFIG_FILE = Path.home() / ".telegram_downloader_config.json"

@dataclass
class AppConfig:
    namespace: str = "default"
    download_dir: str = "/sdcard/Download" if os.path.exists("/sdcard") else str(Path.home() / "Downloads")
    proxy: str = ""

def load_config() -> AppConfig:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AppConfig(**data)
        except Exception:
            pass
    config = AppConfig()
    save_config(config)
    return config

def save_config(config: AppConfig) -> bool:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(asdict(config), f, indent=2)
        return True
    except Exception:
        return False
                
