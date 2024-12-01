# V0.0.15
import os
import sys
from win32com.shell import shell
from core.logging_utils import LoggerSetup
from core.webhook_manager import WebhookManager
from core.config_manager import ConfigManager
from core.file_utils import FileUtils
from core.server_monitor import ServerMonitor

# Define base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'config.json')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

def main():
    """Main function"""
    # Initialize logger
    logger = LoggerSetup.setup_logger('ServerMonitor', LOGS_DIR, 'server_monitor.log')
    
    # Initialize configuration
    config_manager = ConfigManager(CONFIG_PATH, logger)
    
    # Check administrator privileges if firewall is enabled
    if config_manager.get_firewall_enabled() and not shell.IsUserAnAdmin():
        logger.error("Script needs administrator privileges when firewall management is enabled.")
        print("This script needs to be run with administrator privileges when firewall management is enabled.")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Initialize webhook manager
    webhook_manager = WebhookManager(config_path=CONFIG_PATH)
    if webhook_manager.is_enabled():
        webhook_manager.start()
    
    # Get log directory
    log_dir = FileUtils.select_log_directory()
    
    try:
        # Create and start server monitor
        monitor = ServerMonitor(log_dir, webhook_manager, logger, config_manager)
        monitor.start()
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
