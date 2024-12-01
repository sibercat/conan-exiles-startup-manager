# core/server_monitor.py

import time
from watchdog.observers import Observer
from typing import Optional
from core.webhook_manager import WebhookManager
from core.firewall_manager import FirewallManager
from core.zombie_monitor import ZombieProcessMonitor
from core.log_handler import LogHandler
from core.default_config import CONSTANTS

class ServerMonitor:
    def __init__(self, log_dir: str, webhook_manager: WebhookManager, logger, config_manager):
        """
        Initialize server monitor
        
        Args:
            log_dir (str): Path to log directory
            webhook_manager (WebhookManager): Webhook manager instance
            logger: Logger instance
            config_manager (ConfigManager): Configuration manager instance
        """
        self.log_dir = log_dir
        self.webhook_manager = webhook_manager
        self.logger = logger
        self.config_manager = config_manager
        
        # Load configurations
        self.firewall_enabled = config_manager.get_firewall_enabled()
        self.ports = config_manager.get_ports()
        self.startup_delay = config_manager.get_startup_delay()
        self.messages = config_manager.get_messages()
        self.zombie_config = config_manager.get_zombie_config()
        
        # Initialize components
        self.firewall_manager = FirewallManager(logger, self.firewall_enabled)
        self.observer = Observer()
        self.zombie_monitor: Optional[ZombieProcessMonitor] = None
        
        # Initial setup
        if self.firewall_enabled:
            self.logger.info("Initial port blocking...")
            self.firewall_manager.block_ports(self.ports)
            
    def _setup_zombie_monitor(self):
        """Setup zombie process monitoring"""
        if self.zombie_config.get('enabled', True):
            def on_zombie_detected(pid):
                if self.webhook_manager:
                    self.webhook_manager.send_message(self.messages.get("zombie_detected"))
                    
            self.zombie_monitor = ZombieProcessMonitor(
                CONSTANTS["SERVER_PROCESS_NAME"],
                timeout_minutes=self.zombie_config.get('timeout_minutes', 5),
                logger=self.logger,
                on_zombie_detected=on_zombie_detected
            )
            
            self.logger.info(f"Zombie detection enabled (timeout: {self.zombie_config.get('timeout_minutes', 5)} minutes)")

    def start(self):
        """Start server monitoring"""
        # Setup log handler
        event_handler = LogHandler(
            self.log_dir, 
            self.firewall_manager, 
            self.webhook_manager,
            self.logger, 
            self.ports, 
            self.startup_delay, 
            self.messages
        )
        
        # Setup zombie monitoring
        self._setup_zombie_monitor()
        
        # Setup file watching
        self.observer.schedule(event_handler, path=self.log_dir, recursive=False)
        self.observer.start()

        self.logger.info(f"Monitoring logs directory: {self.log_dir}")
        self.logger.info("Firewall management is " + ("enabled" if self.firewall_enabled else "disabled"))
        print("\nPress Ctrl+C to stop monitoring...")
        
        if self.webhook_manager and self.webhook_manager.is_enabled():
            self.webhook_manager.send_message(self.messages.get("startup"))

        try:
            while True:
                if self.zombie_monitor and self.zombie_config.get('enabled', True):
                    self.zombie_monitor.check_process_state()
                    if (self.zombie_config.get('auto_kill', True) 
                        and self.zombie_monitor.zombie_detected):
                        if self.zombie_monitor.force_kill_zombie():
                            self.webhook_manager.send_message(self.messages.get("zombie_killed"))
                time.sleep(self.zombie_config.get('check_interval_seconds', 30))
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop server monitoring"""
        self.logger.info("Stopping server monitoring...")
        self.observer.stop()
        
        if self.firewall_enabled:
            self.logger.info("Ensuring ports are allowed before exit...")
            self.firewall_manager.allow_ports(self.ports)
            
        if self.webhook_manager:
            self.webhook_manager.send_message(self.messages.get("monitor_stop"))
            self.webhook_manager.stop()
        
        self.observer.join()