# core/logging_utils.py
import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from typing import Optional

class LoggerSetup:
    DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DEFAULT_MAX_BYTES = 5 * 1024 * 1024  # 5MB
    DEFAULT_BACKUP_COUNT = 5
    
    @staticmethod
    def setup_logger(
        logger_name: str,
        log_dir: str,
        log_file_name: str,
        log_level: int = logging.INFO,
        format_string: Optional[str] = None,
        max_bytes: int = DEFAULT_MAX_BYTES,
        backup_count: int = DEFAULT_BACKUP_COUNT
    ) -> logging.Logger:
        """
        Set up a logger with both file and console handlers.
        
        Args:
            logger_name (str): Name of the logger to create/get
            log_dir (str): Directory where log files will be stored
            log_file_name (str): Name of the log file
            log_level (int): Logging level (default: logging.INFO)
            format_string (str, optional): Custom format string for log messages
            max_bytes (int): Maximum size in bytes for each log file
            backup_count (int): Number of backup files to keep
            
        Returns:
            logging.Logger: Configured logger instance
            
        Raises:
            OSError: If log directory creation fails
        """
        # Create logs directory if it doesn't exist
        try:
            os.makedirs(log_dir, exist_ok=True)
        except OSError as e:
            print(f"Error creating log directory: {e}")
            raise

        # Get or create logger
        logger = logging.getLogger(logger_name)
        
        # Only set up handlers if they haven't been set up already
        if not logger.handlers:
            logger.setLevel(log_level)
            
            # Create formatter
            log_formatter = logging.Formatter(
                format_string or LoggerSetup.DEFAULT_FORMAT
            )
            
            # Set up file handler
            log_file_path = os.path.join(log_dir, log_file_name)
            file_handler = RotatingFileHandler(
                log_file_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(log_formatter)
            logger.addHandler(file_handler)
            
            # Set up console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(log_formatter)
            logger.addHandler(console_handler)
            
        return logger

    @staticmethod
    def get_logger(logger_name: str) -> Optional[logging.Logger]:
        """
        Get an existing logger by name.
        
        Args:
            logger_name (str): Name of the logger to retrieve
            
        Returns:
            Optional[logging.Logger]: The logger if it exists, None otherwise
        """
        return logging.getLogger(logger_name) if logger_name in logging.root.manager.loggerDict else None