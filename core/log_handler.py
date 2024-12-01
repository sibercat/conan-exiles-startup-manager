# core/log_handler.py

from watchdog.events import FileSystemEventHandler
import os
import time
from typing import List, Dict, Optional
from core.webhook_manager import WebhookManager
from core.default_config import CONSTANTS

# Import constants
SERVER_STARTING_STRING = CONSTANTS["LOG_PATTERNS"]["SERVER_STARTING"]
LOAD_COMPLETE_STRING = CONSTANTS["LOG_PATTERNS"]["LOAD_COMPLETE"]
SERVER_EXIT_WARNING = CONSTANTS["LOG_PATTERNS"]["SERVER_EXIT_WARNING"]
SERVER_NETWORK_DOWN = CONSTANTS["LOG_PATTERNS"]["SERVER_NETWORK_DOWN"]
SERVER_STOPPED_STRING = CONSTANTS["LOG_PATTERNS"]["SERVER_STOPPED"]

class LogHandler(FileSystemEventHandler):
    def __init__(self, log_dir: str, firewall_manager, webhook_manager: Optional[WebhookManager], 
                 logger, ports: List[Dict[str, str]], startup_delay: int, 
                 messages: Dict[str, str]):
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
        """Safely send webhook message"""
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
            if not self.server_exiting:
                self.logger.info("Server shutdown detected without warning...")
                self._send_webhook_message("shutdown_warning")
                self.server_exiting = True
            
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
            self.is_initial_scan = False
            self.logger.info("New server instance detected")
            self.firewall_manager.block_ports(self.ports)

    def on_modified(self, event):
        """Handle log file modifications"""
        if not event.src_path.endswith("ConanSandbox.log"):
            return

        try:
            current_size = os.path.getsize(event.src_path)
            
            if current_size < self.last_file_size and not self.is_initial_scan:
                self.logger.info("Log file rotation detected")
                self.load_complete = False
                self.server_exiting = False
                self.server_stopped = False
                self.server_starting = False
                self.network_shutdown = False
                self.last_processed_line = 0
            
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