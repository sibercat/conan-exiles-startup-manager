# V0.0.8
import subprocess
import time
from win32com.shell import shell
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import tkinter as tk
from tkinter import filedialog
import os
import logging
from core.webhook_manager import WebhookManager  # Changed from discord_manager import
from logging.handlers import RotatingFileHandler
import sys
import json

# Define base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'config.json')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Firewall rule names
RULE_NAME_PREFIX = "GameServerControl"

# Default ports configuration
DEFAULT_PORTS = [
    {"port": 7777, "proto": "UDP"},
    {"port": 7777, "proto": "TCP"},
    {"port": 7778, "proto": "UDP"},
    {"port": 27015, "proto": "UDP"},
    {"port": 25575, "proto": "TCP"}
]

# Default messages
DEFAULT_MESSAGES = {
    "startup": "[START] Server monitor starting up...",
    "loading": "[UPDATE] Server is starting up... Ports blocked for safety.",
    "ready": "[SUCCESS] Server is fully loaded and ready for connections!",
    "shutdown": "[WARNING] Server is shutting down...",
    "monitor_stop": "[STOP] Server monitor shutting down..."
}

def get_ports_from_config():
    """Get ports configuration from config file"""
    try:
        with open(CONFIG_PATH, 'r') as config_file:
            config = json.load(config_file)
            if 'server' in config and 'ports' in config['server']:
                return config['server']['ports']
            return DEFAULT_PORTS
    except Exception as e:
        print(f"Error reading ports from config: {e}")
        return DEFAULT_PORTS

def get_startup_delay():
    """Get startup delay from config file"""
    try:
        with open(CONFIG_PATH, 'r') as config_file:
            config = json.load(config_file)
            if 'server' in config and 'startup_delay' in config['server']:
                return int(config['server']['startup_delay'])
            return 0  # Default to no delay if not specified
    except Exception as e:
        print(f"Error reading startup delay from config: {e}")
        return 0  # Default to no delay on error

def get_messages_from_config():
    """Get Discord messages from config file"""
    try:
        with open(CONFIG_PATH, 'r') as config_file:
            config = json.load(config_file)
            if 'server' in config and 'messages' in config['server']:
                return config['server']['messages']
            return DEFAULT_MESSAGES
    except Exception as e:
        print(f"Error reading messages from config: {e}")
        return DEFAULT_MESSAGES

def setup_logging():
    """Setup logging configuration"""
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)

    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = os.path.join(LOGS_DIR, 'server_monitor.log')
    
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=5*1024*1024,  # 5MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)

    logger = logging.getLogger('ServerMonitor')
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

def select_log_directory():
    """Select the Conan Exiles log directory"""
    print("\nPlease select your Conan Exiles logs folder.")
    print("It's usually located in: <Your Server Path>/ConanSandbox/Saved/Logs/")
    
    root = tk.Tk()
    root.withdraw()
    
    dir_path = filedialog.askdirectory(
        title="Select Conan Exiles Logs Directory"
    )
    
    if not dir_path:
        print("No directory selected. Exiting...")
        exit()
        
    if not os.path.exists(dir_path):
        print("Selected directory does not exist. Exiting...")
        exit()
        
    return dir_path

def block_ports(ports):
    """Block configured ports using Windows Firewall"""
    try:
        for port_info in ports:
            rule_name = f"{RULE_NAME_PREFIX}_{port_info['port']}_{port_info['proto']}"
            cmd = f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=block protocol={port_info["proto"]} localport={port_info["port"]}'
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("All ports blocked.")
    except subprocess.CalledProcessError as e:
        print(f"Error blocking ports: {e}")

def allow_ports(ports):
    """Allow configured ports by removing blocking rules"""
    try:
        for port_info in ports:
            rule_name = f"{RULE_NAME_PREFIX}_{port_info['port']}_{port_info['proto']}"
            cmd = f'netsh advfirewall firewall delete rule name="{rule_name}"'
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("All ports allowed.")
    except subprocess.CalledProcessError as e:
        print(f"Error allowing ports: {e}")

class LogHandler(FileSystemEventHandler):
    def __init__(self, log_dir, webhook_manager=None, logger=None, ports=None, startup_delay=0, messages=None):
        self.load_complete = False
        self.server_exiting = False
        self.log_dir = log_dir
        self.current_log_file = None
        self.LOAD_COMPLETE_STRING = "WorldPersistenceDone"
        self.SERVER_EXIT_STRING = "LogExit: Preparing to exit"
        self.webhook = webhook_manager  # Changed from discord to webhook
        self.logger = logger or logging.getLogger('ServerMonitor')
        self.ports = ports
        self.startup_delay = startup_delay
        self.messages = messages or DEFAULT_MESSAGES

    def on_created(self, event):
        """Handle new log file creation"""
        if event.src_path.endswith("ConanSandbox.log"):
            self.logger.info(f"New log file detected: {event.src_path}")
            print(f"\nNew log file detected: {event.src_path}")
            self.current_log_file = event.src_path
            self.load_complete = False
            self.server_exiting = False
            self.logger.info("Resetting port status due to new log file...")
            print("Resetting port status due to new log file...")
            block_ports(self.ports)
            if self.webhook:
                self.webhook.send_message(self.messages.get("loading"))

    def on_modified(self, event):
        """Handle log file modifications"""
        if event.src_path.endswith("ConanSandbox.log"):
            try:
                with open(event.src_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-100:]
                    for line in reversed(lines):
                        if self.LOAD_COMPLETE_STRING in line and not self.load_complete:
                            if self.startup_delay > 0:
                                self.logger.info(f"Server loaded. Waiting {self.startup_delay} seconds before allowing connections...")
                                print(f"\nServer loaded. Waiting {self.startup_delay} seconds before allowing connections...")
                                time.sleep(self.startup_delay)

                            self.logger.info("Server fully loaded. Allowing connections...")
                            print("Server fully loaded. Allowing connections...")
                            allow_ports(self.ports)
                            self.load_complete = True
                            self.server_exiting = False
                            if self.webhook:
                                self.webhook.send_message(self.messages.get("ready"))
                            break
                        elif self.SERVER_EXIT_STRING in line and not self.server_exiting:
                            self.logger.info("Server is shutting down. Blocking ports...")
                            print("Server is shutting down. Blocking ports...")
                            block_ports(self.ports)
                            self.load_complete = False
                            self.server_exiting = True
                            if self.webhook:
                                self.webhook.send_message(self.messages.get("shutdown"))
                            break
            except Exception as e:
                self.logger.error(f"Error reading log file: {e}")
                print(f"Error reading log file: {e}")

def monitor_server(log_dir, webhook_manager, logger, ports, startup_delay, messages):
    """Main server monitoring function"""
    event_handler = LogHandler(log_dir, webhook_manager, logger, ports, startup_delay, messages)
    observer = Observer()
    
    observer.schedule(event_handler, path=log_dir, recursive=False)
    observer.start()

    logger.info(f"Monitoring logs directory: {log_dir}")
    print(f"\nMonitoring logs directory: {log_dir}")
    print("Press Ctrl+C to stop monitoring...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping server monitoring...")
        print("\nStopping server monitoring...")
        observer.stop()
        logger.info("Ensuring ports are allowed before exit...")
        print("Ensuring ports are allowed before exit...")
        allow_ports(ports)
        if webhook_manager:
            webhook_manager.send_message(messages.get("monitor_stop"))
            webhook_manager.stop()
    
    observer.join()

def main():
    """Main function"""
    logger = setup_logging()

    if not shell.IsUserAnAdmin():
        logger.error("Script needs administrator privileges.")
        print("This script needs to be run with administrator privileges.")
        input("Press Enter to exit...")
        exit()

    # Load configurations
    ports = get_ports_from_config()
    startup_delay = get_startup_delay()
    messages = get_messages_from_config()
    
    if startup_delay > 0:
        logger.info(f"Configured startup delay: {startup_delay} seconds")
        print(f"\nConfigured startup delay: {startup_delay} seconds")
    
    webhook_manager = WebhookManager(config_path=CONFIG_PATH)  # Changed from DiscordManager
    if webhook_manager.is_enabled():
        webhook_manager.start()
    
    log_dir = select_log_directory()
    
    logger.info("Initial port blocking...")
    print("\nInitial port blocking...")
    block_ports(ports)
    
    if webhook_manager and webhook_manager.is_enabled():
        webhook_manager.send_message(messages.get("startup"))
    
    logger.info("Starting server monitoring...")
    print("\nStarting server monitoring...")
    
    try:
        monitor_server(log_dir, webhook_manager, logger, ports, startup_delay, messages)
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"An error occurred: {e}")
    finally:
        if webhook_manager and webhook_manager.is_enabled():
            webhook_manager.stop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {e}")
        logging.getLogger('ServerMonitor').error(f"Fatal error: {e}")
