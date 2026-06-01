import sys
import argparse
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from netlink_tray.config import load_config, create_default_config
from netlink_tray.ui import NetlinkTray

def create_desktop_files():
    exec_path = str(Path.home() / ".local" / "bin" / "netlink-tray")
    
    desktop_content = f"""[Desktop Entry]
Type=Application
Exec={exec_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Netlink Tray
Comment=TCP/UDP port monitor via Netlink
Icon=network-transmit-receive
"""
    # Create in autostart for running at login
    autostart_dir = Path.home() / ".config" / "autostart"
    autostart_dir.mkdir(parents=True, exist_ok=True)
    autostart_file = autostart_dir / "netlink-tray.desktop"
    with open(autostart_file, "w", encoding="utf-8") as f:
        f.write(desktop_content)
    print(f"Created autostart entry at {autostart_file}")

def handle_setup():
    print("Setting up NetlinkTray...")
    create_default_config()
    create_desktop_files()
    print("Setup completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="Netlink Tray - Port Monitor")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    setup_parser = subparsers.add_parser("setup", help="Initialize configuration and desktop files")
    
    args = parser.parse_args()
    
    if args.command == "setup":
        handle_setup()
        sys.exit(0)
        
    # Standard run
    config = load_config()
    port = config.get("port", 2222)
    interval = config.get("polling_interval_ms", 1500)
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    monitor = NetlinkTray(port=port, polling_interval_ms=interval)
    monitor.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
