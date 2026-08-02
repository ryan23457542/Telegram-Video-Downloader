import sys
import os
import time
import subprocess
from pathlib import Path
from utils.ansi import ANSI
from utils.helpers import check_tdl_installed, force_unlock_tdl_database, test_proxy_reachable, last_meaningful_line
from ui.box import Spinner
from config import AppConfig, save_config

class AccountManager:
    @staticmethod
    def get_account_status(namespace: str, proxy: str = "") -> tuple[bool, str]:
        if not check_tdl_installed():
            return False, "TDL engine not installed"

        ns_to_check = namespace if namespace and namespace.strip() else "default"

        if proxy:
            reachable, detail = test_proxy_reachable(proxy, timeout=4.0)
            if not reachable:
                return False, f"Proxy unreachable ({proxy})"

        try:
            cmd = ["tdl", "--ns", ns_to_check]
            if proxy:
                cmd += ["--proxy", proxy]
            cmd += ["chat", "ls", "-f", "false", "-o", "json"]
            with Spinner("Checking account status..."):
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            if res.returncode == 0:
                return True, "Logged In"
            if "timeout" in (res.stderr or "").lower():
                return False, "Connection timeout (check proxy/network)"
            reason = last_meaningful_line(res.stderr)
            return False, f"Not Logged In ({reason})" if reason else "Not Logged In / Session Expired"
        except subprocess.TimeoutExpired:
            return False, "Connection timeout (check proxy/network)"
        except Exception:
            return False, "Session Status Unknown"

    @staticmethod
    def detect_namespaces() -> list[str]:
        tdl_data_dir = Path.home() / ".tdl" / "data"
        if not tdl_data_dir.exists() or not tdl_data_dir.is_dir():
            return []
        
        namespaces = []
        try:
            for item in tdl_data_dir.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    namespaces.append(item.name)
        except Exception:
            pass
        return sorted(namespaces)

    @staticmethod
    def verify_namespace(namespace: str, proxy: str = "", retries: int = 3) -> bool:
        ns_to_check = namespace if namespace and namespace.strip() else "default"
        
        cmd = ["tdl", "--ns", ns_to_check]
        if proxy:
            cmd += ["--proxy", proxy]
        cmd += ["chat", "ls", "-f", "false", "-o", "json"]
        
        for attempt in range(retries):
            force_unlock_tdl_database()
            try:
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=12)
                if res.returncode == 0:
                    return True
            except Exception:
                pass
            if attempt < retries - 1:
                time.sleep(1.5)
        return False

    @staticmethod
    def auto_detect_and_load(config: AppConfig) -> bool:
        if config.namespace and AccountManager.verify_namespace(config.namespace, config.proxy):
            return True

        detected = AccountManager.detect_namespaces()
        for ns in detected:
            if ns == config.namespace:
                continue
            if AccountManager.verify_namespace(ns, config.proxy):
                config.namespace = ns
                save_config(config)
                return True

        config.namespace = "default"
        save_config(config)
        return False

    @staticmethod
    def login_menu(config: AppConfig):
        os.system("clear")
        sys.stdout.write(ANSI.SHOW_CURSOR)
        print(f"\n{ANSI.BOLD}{ANSI.BRIGHT_CYAN}🔐 TELEGRAM LOGIN MANAGER{ANSI.RESET}")
        
        detected = AccountManager.detect_namespaces()
        if detected:
            print(f"\n{ANSI.BOLD}Existing Namespaces Detected:{ANSI.RESET}")
            for idx, ns in enumerate(detected, start=1):
                is_active = f" {ANSI.BRIGHT_GREEN}(Current){ANSI.RESET}" if ns == config.namespace else ""
                print(f" [{idx}] Switch to: {ns}{is_active}")
            print(f" [{len(detected) + 1}] Create / Login New Namespace")
            print(f" [{len(detected) + 2}] Login Current Namespace ({config.namespace or 'default'})")
            print(f" [{len(detected) + 3}] Back")
            
            choice = input(f"\nSelect Option (1-{len(detected) + 3}): ").strip()
            
            if choice.isdigit():
                idx_val = int(choice)
                if 1 <= idx_val <= len(detected):
                    target_ns = detected[idx_val - 1]
                    print(f"\n{ANSI.DIM}Verifying session for namespace '{target_ns}'...{ANSI.RESET}")
                    if AccountManager.verify_namespace(target_ns, config.proxy):
                        config.namespace = target_ns
                        save_config(config)
                        print(f"{ANSI.BRIGHT_GREEN}✔ Switched to namespace '{target_ns}'.{ANSI.RESET}")
                    else:
                        print(f"{ANSI.BRIGHT_RED}✘ Session invalid or expired for '{target_ns}'.{ANSI.RESET}")
                    time.sleep(1.5)
                    return
                elif idx_val == len(detected) + 1:
                    new_ns = input("Enter new namespace name: ").strip()
                    if not new_ns:
                        print(f"{ANSI.BRIGHT_RED}Namespace cannot be empty.{ANSI.RESET}")
                        time.sleep(1)
                        return
                    target_ns = new_ns
                elif idx_val == len(detected) + 2:
                    target_ns = config.namespace or "default"
                elif idx_val == len(detected) + 3:
                    return
                else:
                    print(f"{ANSI.BRIGHT_RED}Invalid option.{ANSI.RESET}")
                    time.sleep(1)
                    return
            else:
                print(f"{ANSI.BRIGHT_RED}Invalid option.{ANSI.RESET}")
                time.sleep(1)
                return
        else:
            target_ns = input("Enter namespace name for login (default: 'default'): ").strip()
            if not target_ns:
                target_ns = "default"

        AccountManager._perform_login(target_ns, config)

    @staticmethod
    def _perform_login(namespace: str, config: AppConfig):
        os.system("clear")
        target_ns = namespace if namespace and namespace.strip() else "default"
        print(f"\n{ANSI.BOLD}{ANSI.BRIGHT_CYAN}🔐 TELEGRAM LOGIN: {target_ns}{ANSI.RESET}")
        print(" [1] Login via Phone & OTP Code\n [2] Login via QR Code\n [3] Back")

        choice = input(f"\nSelect Mode (1-3): ").strip()

        if choice in ["1", "2"]:
            if config.proxy:
                print(f"\n{ANSI.DIM}Testing proxy reachability...{ANSI.RESET}")
                reachable, detail = test_proxy_reachable(config.proxy, timeout=5.0)
                if not reachable:
                    print(f"{ANSI.BRIGHT_RED}✘ Proxy '{config.proxy}' is not reachable: {detail}{ANSI.RESET}")
                    print(f"{ANSI.DIM}Free/public proxies are frequently dead. Try a different one,")
                    print(f"or a personal VPN's local SOCKS5 port, then try again.{ANSI.RESET}")
                    cont = input(f"\nTry logging in anyway? (y/N): ").strip().lower()
                    if cont != "y":
                        return
                else:
                    print(f"{ANSI.BRIGHT_GREEN}✔ Proxy is reachable.{ANSI.RESET}")
                    time.sleep(0.5)

            force_unlock_tdl_database()

            os.system("clear")
            print(f"{ANSI.BRIGHT_YELLOW}Starting Telegram Login...{ANSI.RESET}\n")
            if config.proxy:
                print(f"{ANSI.DIM}Using proxy: {config.proxy}{ANSI.RESET}")
                print(f"{ANSI.DIM}(Slow/free proxies can take 30-60s+ before tdl shows the phone")
                print(f"number prompt below. If nothing appears after ~1 minute, press")
                print(f"Ctrl+C and try a different proxy.){ANSI.RESET}\n")

            mode_flag = "code" if choice == "1" else "qr"

            # TDL CLI တွင် namespace အတွက် --ns flag သို့မဟုတ် -n flag ကို တိကျစွာသုံးရန် ပြင်ထားသည်
            cmd = ["tdl", "--ns", target_ns]
            if config.proxy:
                cmd += ["--proxy", config.proxy]
            cmd += ["login", "-T", mode_flag]
            
            try:
                res = subprocess.run(cmd)
                if res.returncode == 0:
                    print(f"\n{ANSI.DIM}Validating new session...{ANSI.RESET}")
                    time.sleep(1.5)
                    if AccountManager.verify_namespace(target_ns, config.proxy, retries=3):
                        config.namespace = target_ns
                        save_config(config)
                        print(f"{ANSI.BRIGHT_GREEN}✔ Login successful and namespace saved!{ANSI.RESET}")
                    else:
                        print(f"{ANSI.BRIGHT_RED}✘ Login command finished but session validation failed.{ANSI.RESET}")
                else:
                    print(f"{ANSI.BRIGHT_RED}✘ Login failed (exit code: {res.returncode}). Config not updated.{ANSI.RESET}")
            except FileNotFoundError:
                print(f"{ANSI.BRIGHT_RED}Error: 'tdl' binary not found in PATH.{ANSI.RESET}")
            except KeyboardInterrupt:
                print(f"\n{ANSI.BRIGHT_YELLOW}Login cancelled.{ANSI.RESET}")
            except Exception as e:
                print(f"{ANSI.BRIGHT_RED}An error occurred during login: {e}{ANSI.RESET}")

            input(f"\n{ANSI.BRIGHT_GREEN}Press Enter to return to main menu...{ANSI.RESET}")
        elif choice != "3":
            print(f"{ANSI.BRIGHT_RED}Invalid option.{ANSI.RESET}")
            time.sleep(1)
                
