"""
Bot Supervisor - Process-level monitoring and auto-restart
Handles EPIPE and other low-level crashes by restarting the bot process.
"""

import subprocess
import sys
import time
import threading
from pathlib import Path
from datetime import datetime
from utils.logger import logger


class BotSupervisor:
    """
    Supervises the bot process and automatically restarts it on crashes.
    This catches low-level errors like EPIPE that can't be caught by Python try/except.
    """
    
    MAX_RESTARTS = 5  # Maximum restarts before giving up
    RESTART_COOLDOWN = 10  # Seconds to wait between restarts
    CRASH_WINDOW = 300  # Reset restart count if no crash for 5 minutes
    
    def __init__(self):
        self.process = None
        self.restart_count = 0
        self.last_crash_time = None
        self.running = False
        self.stop_requested = False
        self._lock = threading.Lock()
        self._output_callback = None
        self._status_callback = None
        
    def set_callbacks(self, output_callback=None, status_callback=None):
        """Set callbacks for output and status updates"""
        self._output_callback = output_callback
        self._status_callback = status_callback
    
    def _log(self, log_type: str, message: str):
        """Log with callback support"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[SUPERVISOR {timestamp}] [{log_type.upper()}] {message}")
        
        if self._output_callback:
            self._output_callback(log_type, f"[Supervisor] {message}")
    
    def _update_status(self, status: str):
        """Update status with callback"""
        if self._status_callback:
            self._status_callback(status)
    
    def start(self, bot_script: str = "main.py"):
        """Start the bot with supervision"""
        with self._lock:
            if self.running:
                self._log('warning', 'Bot is already running')
                return False
            
            self.running = True
            self.stop_requested = False
        
        # Start supervisor thread
        supervisor_thread = threading.Thread(
            target=self._supervise_loop,
            args=(bot_script,),
            daemon=True
        )
        supervisor_thread.start()
        return True
    
    def stop(self):
        """Stop the bot gracefully"""
        with self._lock:
            self.stop_requested = True
            
            if self.process and self.process.poll() is None:
                self._log('info', 'Sending stop signal to bot process...')
                try:
                    # On Windows, we can't send SIGINT, so we terminate
                    self.process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        self.process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        self._log('warning', 'Process did not stop gracefully, killing...')
                        self.process.kill()
                        
                except Exception as e:
                    self._log('error', f'Error stopping process: {e}')
            
            self.running = False
            self._update_status('stopped')
    
    def _should_restart(self) -> bool:
        """Determine if we should attempt a restart"""
        if self.stop_requested:
            return False
        
        # Reset counter if enough time has passed since last crash
        if self.last_crash_time:
            elapsed = time.time() - self.last_crash_time
            if elapsed > self.CRASH_WINDOW:
                self._log('info', f'No crashes for {elapsed:.0f}s, resetting restart counter')
                self.restart_count = 0
        
        if self.restart_count >= self.MAX_RESTARTS:
            self._log('error', f'Max restarts ({self.MAX_RESTARTS}) exceeded, giving up')
            return False
        
        return True
    
    def _supervise_loop(self, bot_script: str):
        """Main supervision loop that handles restarts"""
        self._log('info', f'🚀 Supervisor starting for {bot_script}')
        self._update_status('starting')
        
        while not self.stop_requested:
            try:
                # Start the bot process
                self._log('info', f'▶️ Starting bot process (attempt {self.restart_count + 1})')
                self._update_status('running')
                
                # Run the bot as a subprocess
                self.process = subprocess.Popen(
                    [sys.executable, bot_script],
                    cwd=Path(__file__).parent.parent,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1  # Line buffered
                )
                
                # Stream output
                if self.process.stdout:
                    for line in self.process.stdout:
                        line = line.strip()
                        if line:
                            print(line)  # Echo to console
                            if self._output_callback:
                                # Detect log type from line content
                                log_type = 'info'
                                if 'ERROR' in line or '❌' in line:
                                    log_type = 'error'
                                elif 'WARNING' in line or '⚠️' in line:
                                    log_type = 'warning'
                                elif 'SUCCESS' in line or '✅' in line or '🎉' in line:
                                    log_type = 'success'
                                self._output_callback(log_type, line)
                
                # Wait for process to complete
                exit_code = self.process.wait()
                
                # Check exit status
                if exit_code == 0:
                    self._log('success', '✅ Bot completed successfully!')
                    self._update_status('completed')
                    break
                elif self.stop_requested:
                    self._log('info', '⏹️ Bot stopped by user')
                    self._update_status('stopped')
                    break
                else:
                    # Crash detected
                    self.last_crash_time = time.time()
                    self.restart_count += 1
                    self._log('error', f'💥 Bot crashed with exit code {exit_code}')
                    self._update_status('crashed')
                    
                    if self._should_restart():
                        self._log('info', f'🔄 Restarting in {self.RESTART_COOLDOWN}s... (attempt {self.restart_count}/{self.MAX_RESTARTS})')
                        self._update_status('restarting')
                        time.sleep(self.RESTART_COOLDOWN)
                    else:
                        self._log('error', '❌ Not restarting - max attempts exceeded or stop requested')
                        break
                        
            except Exception as e:
                self._log('error', f'Supervisor error: {e}')
                self.last_crash_time = time.time()
                self.restart_count += 1
                
                if self._should_restart():
                    self._log('info', f'🔄 Restarting after error in {self.RESTART_COOLDOWN}s...')
                    time.sleep(self.RESTART_COOLDOWN)
                else:
                    break
        
        with self._lock:
            self.running = False
            self.process = None
        
        self._log('info', '🏁 Supervisor stopped')
    
    def is_running(self) -> bool:
        """Check if the bot is currently running"""
        with self._lock:
            return self.running and self.process is not None and self.process.poll() is None
    
    def get_status(self) -> dict:
        """Get current supervisor status"""
        with self._lock:
            return {
                'running': self.running,
                'restart_count': self.restart_count,
                'max_restarts': self.MAX_RESTARTS,
                'stop_requested': self.stop_requested,
                'process_alive': self.process is not None and self.process.poll() is None
            }


# Global supervisor instance
bot_supervisor = BotSupervisor()


def run_with_supervision():
    """Run main.py with supervision - used for standalone execution"""
    supervisor = BotSupervisor()
    
    def output_callback(log_type, message):
        # Just print, already handled in loop
        pass
    
    supervisor.set_callbacks(output_callback=output_callback)
    supervisor.start("main.py")
    
    try:
        # Keep main thread alive
        while supervisor.is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping supervisor...")
        supervisor.stop()


if __name__ == "__main__":
    run_with_supervision()
