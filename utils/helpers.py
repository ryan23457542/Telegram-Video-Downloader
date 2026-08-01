import os
import shutil
import subprocess
import time
from pathlib import Path

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
        
