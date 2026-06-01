import os
import sys
import tomllib
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "netlinkTray"
CONFIG_FILE = CONFIG_DIR / "config.toml"

def load_config():
    if not CONFIG_FILE.exists():
        print(f"Error: Configuration file not found at {CONFIG_FILE}", file=sys.stderr)
        print("Please run 'netlink-tray setup' to initialize the application.", file=sys.stderr)
        sys.exit(1)
        
    try:
        with open(CONFIG_FILE, "rb") as f:
            config = tomllib.load(f)
            return config
    except Exception as e:
        print(f"Error reading config file: {e}", file=sys.stderr)
        sys.exit(1)

def create_default_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    if not CONFIG_FILE.exists():
        default_config = """# NetlinkTray Configuration
port = 2222
polling_interval_ms = 1500
"""
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(default_config)
        print(f"Created default configuration at {CONFIG_FILE}")
    else:
        print(f"Configuration already exists at {CONFIG_FILE}")
