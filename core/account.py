import sys
import os
import re
import time
import subprocess
from utils.ansi import ANSI
from utils.helpers import check_tdl_installed, force_unlock_tdl_database, test_proxy_reachable
from ui.box import Spinner

class AccountManager:
    @staticmethod
    def get_account_status(namespace: str, proxy: str = "") -> tuple[bool, str]:
        if not check_tdl_installed():
            return False, "TDL engine not installed"

        if proxy:
            reachable, detail = test_proxy_reachable(proxy, timeout=4.0)
            if not reachable:
                return False, f"Proxy unreachable ({proxy})"

        try:
            cmd = ["tdl", "-n", namespace]
            if proxy:
                cmd += ["--proxy", proxy]
            cmd += ["user", "me"]
            with Spinner("Checking account status..."):
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=8)
            if res.returncode == 0 and res.stdout.strip():
                match = re.search(r"(?:ID|Name|Phone):\s*(.+)", res.stdout)
                return True, match.group(1).strip() if match else "Logged In"
            if "timeout" in (res.stderr or "").lower():
                return False, "Connection timeout (check proxy/network)"
            return False, "Not Logged In"
        except subprocess.TimeoutExpired:
            return False, "Connection timeout (check proxy/network)"
        except Exception:
            return False, "Session Status Unknown"

    @staticmethod
    def login_menu(namespace: str, proxy: str = ""):
        os.system("clear")
        sys.stdout.write(ANSI.SHOW_CURSOR)
        print(f"\n{ANSI.BOLD}{ANSI.BRIGHT_CYAN}🔐 TELEGRAM LOGIN MANAGER{ANSI.RESET}")
        print(" [1] Login via Phone & OTP Code\n [2] Login via QR Code\n [3] Back")

        choice = input(f"\nSelect Mode (1-3): ").strip()

        if choice in ["1", "2"]:
            if proxy:
                print(f"\n{ANSI.DIM}Testing proxy reachability...{ANSI.RESET}")
                reachable, detail = test_proxy_reachable(proxy, timeout=5.0)
                if not reachable:
                    print(f"{ANSI.BRIGHT_RED}✘ Proxy '{proxy}' is not reachable: {detail}{ANSI.RESET}")
                    print(f"{ANSI.DIM}Free/public proxies are frequently dead. Try a different one,")
                    print(f"or a personal VPN's local SOCKS5 port, then try again.{ANSI.RESET}")
                    cont = input(f"\nTry logging in anyway? (y/N): ").strip().lower()
                    if cont != "y":
                        return
                else:
                    print(f"{ANSI.BRIGHT_GREEN}✔ Proxy is reachable.{ANSI.RESET}")
                    time.sleep(0.5)

            # Process နဲ့ Lock များ ရှင်းထုတ်မည်
            force_unlock_tdl_database()

            os.system("clear")
            print(f"{ANSI.BRIGHT_YELLOW}Starting Telegram Login...{ANSI.RESET}\n")
            if proxy:
                print(f"{ANSI.DIM}Using proxy: {proxy}{ANSI.RESET}")
                print(f"{ANSI.DIM}(Slow/free proxies can take 30-60s+ before tdl shows the phone")
                print(f"number prompt below. If nothing appears after ~1 minute, press")
                print(f"Ctrl+C and try a different proxy.){ANSI.RESET}\n")

            # Mode 1 အတွက် -T code (Phone/OTP)
            # Mode 2 အတွက် -T qr (QR Code Scan)
            mode_flag = "code" if choice == "1" else "qr"

            # Use an argument list (not a shell string) so namespace can
            # never be interpreted as shell syntax.
            cmd = ["tdl", "-n", namespace]
            if proxy:
                cmd += ["--proxy", proxy]
            cmd += ["login", "-T", mode_flag]
            try:
                subprocess.run(cmd)
            except FileNotFoundError:
                print(f"{ANSI.BRIGHT_RED}Error: 'tdl' binary not found in PATH.{ANSI.RESET}")
            except KeyboardInterrupt:
                print(f"\n{ANSI.BRIGHT_YELLOW}Login cancelled.{ANSI.RESET}")

            input(f"\n{ANSI.BRIGHT_GREEN}Press Enter to return to main menu...{ANSI.RESET}")
        elif choice != "3":
            print(f"{ANSI.BRIGHT_RED}Invalid option.{ANSI.RESET}")
            time.sleep(1)
