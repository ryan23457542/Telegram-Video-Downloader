#!/usr/bin/env python3
import os
import re
import sys
import time
import subprocess

from utils.ansi import ANSI
from utils.helpers import check_tdl_installed
from ui.box import Box, typewriter
from config import load_config, save_config
from core.account import AccountManager
from core.engine import DownloadEngine

LINK_PATTERN = re.compile(r"^(https?://)?t\.me/", re.IGNORECASE)


def kill_stale_tdl_processes():
    """Background မှာ ငြိနေတဲ့ tdl process များကို ရှင်းထုတ်ပေးသည့် function"""
    try:
        # Termux/Linux မှာ ပိတ်မကျဘဲ ကျန်နေတဲ့ tdl process အားလုံးကို ရှင်းပစ်မည်
        subprocess.run(["pkill", "-9", "-f", "tdl"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        time.sleep(0.5)  # Database lock ပြေသွားအောင် ခဏစောင့်မည်
    except Exception:
        pass


def show_startup_banner():
    os.system("clear")
    box = Box(width=46)
    print(box.top())
    print(box.line(f"{ANSI.BOLD}{ANSI.BRIGHT_MAGENTA}🚀 TELEGRAM DOWNLOADER{ANSI.RESET}"))
    print(box.line(f"{ANSI.DIM}Powered by tdl · v7{ANSI.RESET}"))
    print(box.bottom())
    sys.stdout.write(f"{ANSI.DIM}")
    typewriter("  initializing...", delay=0.02)
    sys.stdout.write(f"{ANSI.RESET}")
    time.sleep(0.25)


def pause(message: str = "Press Enter to continue...", color: str = ANSI.DIM):
    input(f"\n{color}{message}{ANSI.RESET}")


class TelegramDownloaderApp:
    def __init__(self):
        self.config = load_config()

    def render_menu(self, logged_in: bool, status_msg: str):
        os.system("clear")
        box = Box(width=46)
        status_color = ANSI.BRIGHT_GREEN if logged_in else ANSI.BRIGHT_RED

        print(box.top())
        print(box.line(f"{ANSI.BOLD}{ANSI.BRIGHT_MAGENTA}TELEGRAM DOWNLOADER{ANSI.RESET} {ANSI.DIM}v7{ANSI.RESET}"))
        print(box.divider())
        print(box.row("Status", status_msg, status_color))
        print(box.row("Path", self.config.download_dir, ANSI.BRIGHT_YELLOW))
        if self.config.proxy:
            print(box.row("Proxy", self.config.proxy, ANSI.BRIGHT_CYAN))
        print(box.divider())
        print(box.line(f"{ANSI.BRIGHT_WHITE}[1]{ANSI.RESET} Download Link"))
        print(box.line(f"{ANSI.BRIGHT_WHITE}[2]{ANSI.RESET} Login / Switch Account"))
        print(box.line(f"{ANSI.BRIGHT_WHITE}[3]{ANSI.RESET} Change Download Folder"))
        print(box.line(f"{ANSI.BRIGHT_WHITE}[4]{ANSI.RESET} Set Proxy (connection issues)"))
        print(box.line(f"{ANSI.BRIGHT_WHITE}[5]{ANSI.RESET} Exit"))
        print(box.bottom())

    def change_download_folder(self):
        print(f"\n{ANSI.BRIGHT_CYAN}Current folder:{ANSI.RESET} {self.config.download_dir}")
        new_path = input("Enter new download folder (leave empty to cancel): ").strip()
        if not new_path:
            return
        expanded = os.path.expanduser(new_path)
        try:
            os.makedirs(expanded, exist_ok=True)
        except OSError as e:
            print(f"{ANSI.BRIGHT_RED}Could not create/access that folder: {e}{ANSI.RESET}")
            pause()
            return
        self.config.download_dir = expanded
        save_config(self.config)
        print(f"{ANSI.BRIGHT_GREEN}Download folder updated.{ANSI.RESET}")
        pause()

    def change_proxy(self):
        current = self.config.proxy or "(none)"
        print(f"\n{ANSI.BRIGHT_CYAN}Current proxy:{ANSI.RESET} {current}")
        print(f"{ANSI.DIM}Format: socks5://host:port  or  http://host:port")
        print(f"Leave empty to clear, or type 'cancel' to keep it as-is.{ANSI.RESET}")
        new_proxy = input("Enter proxy address: ").strip()
        if new_proxy.lower() == "cancel":
            return
        self.config.proxy = new_proxy
        save_config(self.config)
        if new_proxy:
            print(f"{ANSI.BRIGHT_GREEN}Proxy set to: {new_proxy}{ANSI.RESET}")
        else:
            print(f"{ANSI.BRIGHT_GREEN}Proxy cleared.{ANSI.RESET}")
        pause()

    def handle_download(self, logged_in: bool):
        if not logged_in:
            print(f"{ANSI.BRIGHT_RED}You must log in first.{ANSI.RESET}")
            time.sleep(1.2)
            AccountManager.login_menu(self.config.namespace, self.config.proxy)
            return

        link = input("Enter Telegram Link: ").strip()
        if not link:
            return
        if not LINK_PATTERN.match(link):
            print(f"{ANSI.BRIGHT_RED}That doesn't look like a valid t.me link.{ANSI.RESET}")
            pause()
            return

        try:
            engine = DownloadEngine(link, self.config)
        except Exception as e:
            print(f"{ANSI.BRIGHT_RED}Failed to resolve link: {e}{ANSI.RESET}")
            pause()
            return

        try:
            success = engine.execute()
        except KeyboardInterrupt:
            success = False

        if success:
            print(f"\n{ANSI.BRIGHT_GREEN}✔ Download completed successfully!{ANSI.RESET}")
        else:
            print(f"\n{ANSI.BRIGHT_RED}✘ Download did not complete.{ANSI.RESET}")
        pause()

    def run(self):
        if not check_tdl_installed():
            os.system("clear")
            print(f"{ANSI.BRIGHT_RED}Error: 'tdl' binary is not installed or not in PATH!{ANSI.RESET}")
            print(f"{ANSI.DIM}Install it first, then run this app again.{ANSI.RESET}")
            sys.exit(1)

        kill_stale_tdl_processes()
        show_startup_banner()

        while True:
            logged_in, status_msg = AccountManager.get_account_status(self.config.namespace, self.config.proxy)
            self.render_menu(logged_in, status_msg)

            choice = input("Select Option (1-5): ").strip()

            if choice == "1":
                self.handle_download(logged_in)
            elif choice == "2":
                AccountManager.login_menu(self.config.namespace, self.config.proxy)
            elif choice == "3":
                self.change_download_folder()
            elif choice == "4":
                self.change_proxy()
            elif choice == "5":
                os.system("clear")
                typewriter(f"{ANSI.BRIGHT_CYAN}Goodbye! 👋{ANSI.RESET}", delay=0.02)
                break
            else:
                print(f"{ANSI.BRIGHT_RED}Invalid option, please choose 1-5.{ANSI.RESET}")
                time.sleep(1)


if __name__ == "__main__":
    sys.stdout.write(ANSI.SHOW_CURSOR)
    try:
        app = TelegramDownloaderApp()
        app.run()
    except KeyboardInterrupt:
        sys.stdout.write(ANSI.SHOW_CURSOR)
        print(f"\n{ANSI.BRIGHT_YELLOW}Interrupted. Goodbye!{ANSI.RESET}")
        sys.exit(0)
    finally:
        sys.stdout.write(ANSI.SHOW_CURSOR)
        sys.stdout.flush()
        
