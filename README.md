# 🚀 Telegram Ultra Smart Downloader v1

A high-performance, multi-threaded Telegram downloader CLI built for Termux and Linux. Features live dynamic ANSI dashboard, auto profile selector, and session persistence.

## 🌟 Key Features

- **Multi-threaded Core Engine:** Powered by `tdl` binary for maximum download speeds.
- **Smart Profiles:** Dynamically sets thread and pool counts based on file sizes.
- **Live ANSI Dashboard:** Real-time progress bar, speed tracker, ETA, and ping monitor.
- **Session Persistence:** Config and login sessions are stored safely and locally (`~/.telegram_downloader_config.json`).

## 📁 Project Structure

```text
telegram_downloader/
├── config.py             # Configuration & Persistence
├── main.py               # Main CLI Application Loop
├── utils/
│   ├── ansi.py           # Terminal Color Controls
│   ├── helpers.py        # Bytes/Time Formatting Utilities
│   └── ping.py           # Network Ping Monitor
├── core/
│   ├── account.py        # Session & Login Manager
│   ├── resolver.py       # Link Parsing & Profile Logic
│   └── engine.py         # Subprocess Execution & Live Parser
└── ui/
    └── dashboard.py      # Terminal UI Renderer
