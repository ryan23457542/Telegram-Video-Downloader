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
            # Database lock များကို အရင်ရှင်းထုတ်မည်
            force_unlock_tdl_database()
            
            login_type = "code" if choice == "1" else "qr"
            
            # Terminal ကို ရှင်းပြီး Direct TDL Command သို့ တိုက်ရိုက် လွှဲပေးမည်
            os.system("clear")
            print(f"{ANSI.BRIGHT_YELLOW}Connecting to Telegram Server...{ANSI.RESET}\n")
            
            # --type code အတိုင်း တိုက်ရိုက် run ပေးမည်
            cmd = f"tdl -n {namespace} login --type {login_type}"
            exit_code = os.system(cmd)
            
            if exit_code != 0:
                # အကယ်၍ --type အဆင်မပြေပါက -T ဖြင့် fallback ပြန်စမ်းမည်
                os.system(f"tdl -n {namespace} login -T {login_type}")

            input(f"\n{ANSI.BRIGHT_GREEN}Press Enter to return to menu...{ANSI.RESET}")
            
