import sys
import os
import re
import subprocess
from utils.ansi import ANSI
from utils.helpers import check_tdl_installed, force_unlock_tdl_database

class AccountManager:
    @staticmethod
    def get_account_status(namespace: str) -> tuple[bool, str]:
        if not check_tdl_installed():
            return False, "TDL engine not installed"
        try:
            cmd = ["tdl", "-n", namespace, "user", "me"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                match = re.search(r"(?:ID|Name|Phone):\s*(.+)", res.stdout)
                return True, match.group(1).strip() if match else "Logged In"
            return False, "Not Logged In"
        except Exception:
            return False, "Session Status Unknown"

    @staticmethod
    def login_menu(namespace: str):
        sys.stdout.write(ANSI.SHOW_CURSOR)
        print(f"\n{ANSI.BOLD}{ANSI.BRIGHT_CYAN}🔐 TELEGRAM LOGIN MANAGER{ANSI.RESET}")
        print(" [1] Login via Phone & OTP Code\n [2] Login via QR Code\n [3] Back")
        
        choice = input(f"\nSelect Mode (1-3): ").strip()
        
        if choice in ["1", "2"]:
            # Process နဲ့ Lock များ ရှင်းထုတ်မည်
            force_unlock_tdl_database()
            
            os.system("clear")
            print(f"{ANSI.BRIGHT_YELLOW}Starting Telegram Login...{ANSI.RESET}\n")
            
            # Mode 1 အတွက် -T code (Phone/OTP)
            # Mode 2 အတွက် -T qr (QR Code Scan)
            mode_flag = "code" if choice == "1" else "qr"
            
            # -n {namespace} ရော -T {mode_flag} ရော ပါမှ Termux မှာ အဆင်ပြေမည်
            cmd = f"tdl -n {namespace} login -T {mode_flag}"
            os.system(cmd)

            input(f"\n{ANSI.BRIGHT_GREEN}Press Enter to return to main menu...{ANSI.RESET}")
            
