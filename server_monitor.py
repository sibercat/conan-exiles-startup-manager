# V0.0.12
import subprocess
import time
from win32com.shell import shell
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import tkinter as tk
from tkinter import filedialog
import os
import json
import sys
from typing import List, Dict, Optional
from core.webhook_manager import WebhookManager
from core.logging_utils import LoggerSetup

# Define base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'config.json')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Constants
RULE_NAME_PREFIX = "GameServerControl"
SERVER_STARTING_STRING = "Entered application state 'ConanSandboxStarting'"
LOAD_COMPLETE_STRING = "WorldPersistenceDone"
SERVER_EXIT_WARNING = "LogWindows: FPlatformMisc::RequestExit(0)"
SERVER_NETWORK_DOWN = "LogNet: World NetDriver shutdown"
SERVER_STOPPED_STRING = "Entered application state 'ConanSandboxStopped'"

# Default configurations
DEFAULT_PORTS = [
    {"port": 7777, "proto": "UDP"},
    {"port": 7777, "proto": "TCP"},
    {"port": 7778, "proto": "UDP"},
    {"port": 27015, "proto": "UDP"},
    {"port": 25575, "proto": "TCP"}
]

DEFAULT_MESSAGES = {
    "startup": "[START] Server monitor starting up...",
    "loading": "[UPDATE] Server is starting up...",
    "ready": "[SUCCESS] Server is fully loaded and ready for connections!",
    "shutdown_warning": "[WARNING] Server is preparing to shut down...",
    "network_shutdown": "[WARNING] Server network is shutting down...",
    "shutdown_final": "[WARNING] Server has stopped...",
    "monitor_stop": "[STOP] Server monitor shutting down..."
}

class ConfigManager:
    @staticmethod
    def load_config() -> dict:
        try:
            with open(CONFIG_PATH, 'r') as config_file:
                return json.load(config_file)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    @staticmethod
    def get_firewall_enabled() -> bool:
        config = ConfigManager.load_config()
        return config.get('server', {}).get('firewall_enabled', True)

    @staticmethod
    def get_ports() -> List[Dict[str, str]]:
        config = ConfigManager.load_config()
        return config.get('server', {}).get('ports', DEFAULT_PORTS)

    @staticmethod
    def get_startup_delay() -> int:
        config = ConfigManager.load_config()
        return int(config.get('server', {}).get('startup_delay', 0))

    @staticmethod
    def get_messages() -> Dict[str, str]:
        config = ConfigManager.load_config()
        return config.get('server', {}).get('messages', DEFAULT_MESSAGES)

class FirewallManager:
    def __init__(self, logger, enabled: bool = True):
        self.logger = logger
        self.enabled = enabled

    def block_ports(self, ports: List[Dict[str, str]]) -> None:
        """Block configured ports using Windows Firewall"""
        if not self.enabled:
            self.logger.info("Firewall management disabled, skipping port blocking.")
            return

        try:
            for port_info in ports:
                rule_name = f"{RULE_NAME_PREFIX}_{port_info['port']}_{port_info['proto']}"
                cmd = f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=block protocol={port_info["proto"]} localport={port_info["port"]}'
                subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.logger.info("All ports blocked successfully.")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error blocking ports: {e}")

    def allow_ports(self, ports: List[Dict[str, str]]) -> None:
        """Allow configured ports by removing blocking rules"""
        if not self.enabled:
            self.logger.info("Firewall management disabled, skipping port allowing.")
            return

        try:
            for port_info in ports:
                rule_name = f"{RULE_NAME_PREFIX}_{port_info['port']}_{port_info['proto']}"
                cmd = f'netsh advfirewall firewall delete rule name="{rule_name}"'
                subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.logger.info("All ports allowed successfully.")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error allowing ports: {e}")

class LogHandler(FileSystemEventHandler):
    def __init__(self, log_dir: str, firewall_manager: FirewallManager, webhook_manager: Optional[WebhookManager], 
                 logger, ports: List[Dict[str, str]], startup_delay: int, messages: Dict[str, str]):
        super().__init__()
        
        self.logger = logger
        self.load_complete = False
        self.server_exiting = False
        self.server_stopped = False
        self.log_dir = log_dir
        self.current_log_file = None
        self.webhook = webhook_manager
        self.ports = ports
        self.startup_delay = startup_delay
        self.messages = messages
        self.firewall_manager = firewall_manager
        self.last_processed_line = 0
        self.last_file_size = 0
        self.is_initial_scan = True
        self.server_starting = False
        self.network_shutdown = False
        
        self._initialize_log_file()
        
        self.logger.debug("LogHandler initialized successfully")

    def _initialize_log_file(self):
        """Check for existing ConanSandbox.log file on startup"""
        log_path = os.path.join(self.log_dir, "ConanSandbox.log")
        if os.path.exists(log_path):
            self.logger.info("Found existing log file on startup")
            self.current_log_file = log_path
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    self.last_processed_line = len(lines)
                    self.last_file_size = os.path.getsize(log_path)
            except Exception as e:
                self.logger.error(f"Error reading existing log file: {e}")

    def _send_webhook_message(self, message_key: str) -> None:
        """
        Safely send webhook message
        
        Args:
            message_key (str): Key for the message in self.messages
        """
        if not self.webhook:
            return

        try:
            message = self.messages.get(message_key)
            if not message:
                self.logger.error(f"Message key '{message_key}' not found in configuration")
                return
                
            self.webhook.send_message(message)
        except Exception as e:
            self.logger.error(f"Error sending webhook message: {e}")

    def _handle_server_load(self):
        """Handle server load completion"""
        if self.startup_delay > 0:
            self.logger.info(f"Server loaded. Waiting {self.startup_delay} seconds before allowing connections...")
            time.sleep(self.startup_delay)

        self.logger.info("Server fully loaded. Allowing connections...")
        self.firewall_manager.allow_ports(self.ports)
        self.load_complete = True
        self.server_exiting = False
        self._send_webhook_message("ready")

    def _handle_server_exit_warning(self):
        """Handle initial server exit warning"""
        if not self.server_exiting:
            self.logger.info("Server shutdown initiated...")
            self.server_exiting = True
            self._send_webhook_message("shutdown_warning")

    def _handle_network_shutdown(self):
        """Handle network shutdown state"""
        if self.server_exiting and not self.server_stopped and not self.network_shutdown:
            self.logger.info("Server network is shutting down...")
            self.network_shutdown = True
            self._send_webhook_message("network_shutdown")

    def _handle_server_stopped(self):
        """Handle final server stopped state"""
        if not self.server_stopped:
            # If we didn't get a shutdown warning, send it now
            if not self.server_exiting:
                self.logger.info("Server shutdown detected without warning...")
                self._send_webhook_message("shutdown_warning")
                self.server_exiting = True
            
            # If we didn't get a network shutdown message, send it
            if not self.network_shutdown:
                self.logger.info("Server network shutdown detected...")
                self._send_webhook_message("network_shutdown")
                self.network_shutdown = True
            
            self.logger.info("Server has stopped. Blocking ports...")
            self.firewall_manager.block_ports(self.ports)
            self.load_complete = False
            self.server_stopped = True
            self._send_webhook_message("shutdown_final")

    def on_created(self, event):
        """Handle new log file creation"""
        if event.src_path.endswith("ConanSandbox.log"):
            self.logger.info(f"New log file detected: {event.src_path}")
            self.current_log_file = event.src_path
            self.load_complete = False
            self.server_exiting = False
            self.server_stopped = False
            self.server_starting = False
            self.network_shutdown = False
            self.last_processed_line = 0
            self.last_file_size = 0
            self.is_initial_scan = False  # New file means we're past initial scan
            self.logger.info("New server instance detected")
            self.firewall_manager.block_ports(self.ports)

    def on_modified(self, event):
        """Handle log file modifications"""
        if not event.src_path.endswith("ConanSandbox.log"):
            return

        try:
            current_size = os.path.getsize(event.src_path)
            
            # If file size is smaller than last known size, it's likely a new log file
            if current_size < self.last_file_size and not self.is_initial_scan:
                self.logger.info("Log file rotation detected")
                self.load_complete = False
                self.server_exiting = False
                self.server_stopped = False
                self.server_starting = False
                self.network_shutdown = False
                self.last_processed_line = 0
            
            # Only process file if size has increased
            if current_size > self.last_file_size:
                self._process_log_file(event.src_path)
            
            self.last_file_size = current_size
            self.is_initial_scan = False

        except Exception as e:
            self.logger.error(f"Error processing log file: {e}")

    def _process_log_file(self, file_path: str):
        """Process log file changes"""
        if not os.path.isfile(file_path) or not os.access(file_path, os.R_OK):
            self.logger.error(f"Log file not accessible: {file_path}")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                new_lines = lines[self.last_processed_line:]
                self.last_processed_line = len(lines)

                # Check for server starting first
                for line in new_lines:
                    if SERVER_STARTING_STRING in line and not self.server_starting:
                        self.logger.info("Server is starting up...")
                        self.server_starting = True
                        self._send_webhook_message("loading")
                        break

                # First check for server stop state
                for line in new_lines:
                    if SERVER_STOPPED_STRING in line and not self.server_stopped:
                        self._handle_server_stopped()
                        return

                # Then check other states if server hasn't stopped
                for line in reversed(new_lines[-100:]):
                    if LOAD_COMPLETE_STRING in line and not self.load_complete:
                        self._handle_server_load()
                        break
                    elif SERVER_EXIT_WARNING in line and not self.server_exiting:
                        self._handle_server_exit_warning()
                        break
                    elif SERVER_NETWORK_DOWN in line and self.server_exiting:
                        self._handle_network_shutdown()
                        break

        except Exception as e:
            self.logger.error(f"Error reading log lines: {e}")

def select_log_directory() -> str:
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
        sys.exit(1)
        
    if not os.path.exists(dir_path):
        print("Selected directory does not exist. Exiting...")
        sys.exit(1)
        
    return dir_path

def monitor_server(log_dir: str, webhook_manager: WebhookManager, logger, ports: List[Dict[str, str]], 
                  startup_delay: int, messages: Dict[str, str], firewall_enabled: bool):
    """Main server monitoring function"""
    firewall_manager = FirewallManager(logger, firewall_enabled)
    event_handler = LogHandler(log_dir, firewall_manager, webhook_manager, logger, ports, startup_delay, messages)
    observer = Observer()
    
    observer.schedule(event_handler, path=log_dir, recursive=False)
    observer.start()

    logger.info(f"Monitoring logs directory: {log_dir}")
    logger.info("Firewall management is " + ("enabled" if firewall_enabled else "disabled"))
    print("\nPress Ctrl+C to stop monitoring...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping server monitoring...")
        observer.stop()
        if firewall_enabled:
            logger.info("Ensuring ports are allowed before exit...")
            firewall_manager.allow_ports(ports)
        if webhook_manager:
            webhook_manager.send_message(messages.get("monitor_stop"))
            webhook_manager.stop()
    
    observer.join()

def main():
    """Main function"""
    # Initialize logger
    logger = LoggerSetup.setup_logger('ServerMonitor', LOGS_DIR, 'server_monitor.log')

    # Load configurations
    firewall_enabled = ConfigManager.get_firewall_enabled()
    if firewall_enabled and not shell.IsUserAnAdmin():
        logger.error("Script needs administrator privileges when firewall management is enabled.")
        print("This script needs to be run with administrator privileges when firewall management is enabled.")
        input("Press Enter to exit...")
        sys.exit(1)

    ports = ConfigManager.get_ports()
    startup_delay = ConfigManager.get_startup_delay()
    messages = ConfigManager.get_messages()
    
    if startup_delay > 0:
        logger.info(f"Configured startup delay: {startup_delay} seconds")
    
    webhook_manager = WebhookManager(config_path=CONFIG_PATH)
    if webhook_manager.is_enabled():
        webhook_manager.start()
    
    log_dir = select_log_directory()
    
    firewall_manager = FirewallManager(logger, firewall_enabled)
    if firewall_enabled:
        logger.info("Initial port blocking...")
        firewall_manager.block_ports(ports)
    
    if webhook_manager and webhook_manager.is_enabled():
        webhook_manager.send_message(messages.get("startup"))
    
    try:
        monitor_server(log_dir, webhook_manager, logger, ports, startup_delay, messages, firewall_enabled)
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        if webhook_manager and webhook_manager.is_enabled():
            webhook_manager.stop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {e}")
