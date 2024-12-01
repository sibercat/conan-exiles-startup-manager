# core/zombie_monitor.py
import psutil
import time
from typing import Optional, Callable

class ZombieProcessMonitor:
    def __init__(self, process_name: str, timeout_minutes: int = 5, logger = None, 
                 on_zombie_detected: Optional[Callable] = None):
        """
        Initialize zombie process monitor
        
        Args:
            process_name (str): Name of the process to monitor (e.g. 'ConanSandboxServer-Win64-Shipping.exe')
            timeout_minutes (int): How long to wait before declaring process as zombie
            logger: Logger instance
            on_zombie_detected: Callback function when zombie is detected
        """
        self.process_name = process_name
        self.timeout_seconds = timeout_minutes * 60
        self.logger = logger
        self.on_zombie_detected = on_zombie_detected
        self.last_response_time = None
        self.zombie_detected = False
        
    def _find_server_process(self) -> Optional[psutil.Process]:
        """Find the Conan server process"""
        for proc in psutil.process_iter(['name', 'status']):
            try:
                if proc.name() == self.process_name:
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
        
    def check_process_state(self) -> bool:
        """
        Check if process is responding
        
        Returns:
            bool: True if process is responding, False if zombie/hanging
        """
        proc = self._find_server_process()
        if not proc:
            # Reset state if process not found
            self.last_response_time = None
            self.zombie_detected = False
            return True
            
        try:
            # Check if process is responding
            status = proc.status()
            if status == psutil.STATUS_ZOMBIE:
                if not self.zombie_detected:
                    self.zombie_detected = True
                    self._handle_zombie_process(proc)
                return False
                
            # Check if process is hanging
            if not proc.is_running() or not self.last_response_time:
                self.last_response_time = time.time()
            elif time.time() - self.last_response_time > self.timeout_seconds:
                if not self.zombie_detected:
                    self.zombie_detected = True
                    self._handle_zombie_process(proc)
                return False
                
            # Process is responding, update timestamp
            self.last_response_time = time.time()
            self.zombie_detected = False
            return True
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self.last_response_time = None
            self.zombie_detected = False
            return True
            
    def _handle_zombie_process(self, proc: psutil.Process):
        """Handle detected zombie process"""
        if self.logger:
            self.logger.warning(f"Zombie process detected! PID: {proc.pid}")
            
        if self.on_zombie_detected:
            self.on_zombie_detected(proc.pid)
            
    def force_kill_zombie(self):
        """Force kill zombie process if exists"""
        proc = self._find_server_process()
        if proc and self.zombie_detected:
            try:
                proc.kill()
                if self.logger:
                    self.logger.info(f"Forcefully terminated zombie process (PID: {proc.pid})")
                return True
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                if self.logger:
                    self.logger.error(f"Failed to kill zombie process: {e}")
                return False
        return False