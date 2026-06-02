# Netlink Tray

A lightweight, system tray application that monitors a specific TCP/UDP port using Linux Netlink sockets (`INET_DIAG`). It displays a high-contrast icon in your system tray to indicate whether the monitored port is currently in use or active.

## Features

- **Netlink INET_DIAG:** Uses kernel-level Netlink diagnostic messages rather than spawning external processes like `netstat` or `ss`, providing a highly efficient and fast way to query socket states.
- **Configurable:** Automatically loads the monitored port and polling interval from a user-level configuration file (`~/.config/netlinkTray/config.toml`).
- **System Tray Integration:** Runs silently in the background and displays an intuitive icon in the system tray. The icon visually changes based on the port's activity.
- **Auto-start Support:** Includes a setup command to automatically create desktop entries for application menus and login autostart.

## Requirements

- Linux operating system (requires Netlink socket support)
- Python 3.11 or higher
- PyQt6

## Installation

### Using `pipx` (Recommended)
You can install and isolate the application directly from GitHub using `pipx`:

```bash
pipx install git+https://github.com/arrase/netlinkTray.git
```

### Using `uv`
If you prefer using `uv` for fast Python package management, you can install it globally as a tool:

```bash
uv tool install git+https://github.com/arrase/netlinkTray.git
```

## Setup

Before running the monitor, you must initialize the configuration and desktop files. Run the following command:

```bash
netlink-tray setup
```

This will:
1. Create a default configuration file at `~/.config/netlinkTray/config.toml`.
2. Generate an autostart entry (`~/.config/autostart/netlink-tray.desktop`) so the monitor launches when you log in.

## Configuration

You can edit the configuration file located at `~/.config/netlinkTray/config.toml` to change the monitored port and polling interval:

```toml
# NetlinkTray Configuration
port = 2222
polling_interval_ms = 1500
```

- `port`: The TCP/UDP port number to monitor.
- `polling_interval_ms`: How frequently (in milliseconds) the application queries the Netlink socket.

## Usage

If you have completed the setup, the application will automatically run on startup. You can also start it manually from your application launcher (search for "Netlink Tray") or via terminal:

```bash
netlink-tray
```

To close the monitor, simply right-click the system tray icon and select **"Close Monitor"**.
