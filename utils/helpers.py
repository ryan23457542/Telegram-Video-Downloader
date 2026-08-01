import shutil

def format_bytes(size: float) -> str:
    if size <= 0:
        return "0.00 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def format_time(seconds: float) -> str:
    if seconds <= 0 or seconds > 864000:
        return "--:--"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

def get_terminal_width(default: int = 60) -> int:
    return shutil.get_terminal_size((default, 24)).columns

def check_tdl_installed() -> bool:
    return shutil.which("tdl") is not None
  
