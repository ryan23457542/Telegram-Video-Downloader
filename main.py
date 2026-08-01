#!/usr/bin/env python3
import sys
from utils.ansi import ANSI
from utils.helpers import check_tdl_installed
from config import load_config, save_config
from core.account import AccountManager
from core.engine import DownloadEngine

class TelegramDownloaderApp:
    def __init__(self):
        self.config = load_config()

    def run(self):
        if not check_tdl_installed():
            print(f"{ANSI.BRIGHT_RED}Error: 'tdl' binary is not installed!{ANSI.RESET}")
            sys.exit(1)

        while True:
            logged_in, status_msg = AccountManager.get_account_status(self.config.namespace)
            
            sys.stdout.write(ANSI.SHOW_CURSOR)
            print(f"\n{ANSI.BOLD}{ANSI.BRIGHT_CYAN}TELEGRAM DOWNLOADER v7{ANSI.RESET}")
            print(f" Status : {status_msg}")
            print(f" Path   : {self.config.download_dir}")
            print(" [1] Download Link\n [2] Login Account\n [3] Exit")

            choice = input("Select Option (1-3): ").strip()

            if choice == "1":
                if not logged_in:
                    AccountManager.login_menu(self.config.namespace)
                    continue
                link = input("Enter Telegram Link: ").strip()
                if link:
                    engine = DownloadEngine(link, self.config)
                    engine.execute()
            elif choice == "2":
                AccountManager.login_menu(self.config.namespace)
            elif choice == "3":
                print("Goodbye!")
                break

if __name__ == "__main__":
    app = TelegramDownloaderApp()
    app.run()
                                                                      
