#!/usr/bin/env python
"""
run_supervised.py - Run the Flask app with bot process supervision

This script runs the bot in a supervised subprocess that automatically
restarts on crashes like EPIPE. Use this instead of `python app.py` for
production deployments.

Usage:
    python run_supervised.py

Features:
    - Auto-restart on crash (up to 5 attempts)
    - 10 second cooldown between restarts
    - Preserves progress via progress.json
    - Full log forwarding
"""

import subprocess
import sys
import time
import signal
import os
from datetime import datetime

# Configuration
MAX_RESTARTS = 5
RESTART_COOLDOWN = 10  # seconds
CRASH_WINDOW = 300  # Reset counter if no crash for 5 minutes

class SupervisedRunner:
    """Runs app.py with automatic restart on crash"""
    
    def __init__(self):
        self.process = None
        self.restart_count = 0
        self.last_crash_time = None
        self.running = True
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[SUPERVISOR {timestamp}] {message}")
    
    def should_restart(self):
        if not self.running:
            return False
        
        # Reset counter if enough time passed
        if self.last_crash_time:
            elapsed = time.time() - self.last_crash_time
            if elapsed > CRASH_WINDOW:
                self.log(f"✅ No crashes for {elapsed:.0f}s, resetting restart counter")
                self.restart_count = 0
        
        if self.restart_count >= MAX_RESTARTS:
            self.log(f"❌ Max restarts ({MAX_RESTARTS}) exceeded")
            return False
        
        return True
    
    def run(self):
        self.log("🚀 Supervised Runner Starting")
        self.log(f"📋 Max restarts: {MAX_RESTARTS}, Cooldown: {RESTART_COOLDOWN}s")
        
        while self.running:
            try:
                self.log(f"▶️ Starting Flask app (attempt {self.restart_count + 1}/{MAX_RESTARTS})")
                
                # Start app.py
                self.process = subprocess.Popen(
                    [sys.executable, "app.py"],
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                    # Don't capture stdout/stderr - let it flow to console
                )
                
                # Wait for process to complete
                exit_code = self.process.wait()
                
                if exit_code == 0:
                    self.log("✅ App exited normally")
                    break
                elif not self.running:
                    self.log("⏹️ App stopped by user")
                    break
                else:
                    # Crash detected
                    self.last_crash_time = time.time()
                    self.restart_count += 1
                    self.log(f"💥 App crashed with exit code {exit_code}")
                    
                    if self.should_restart():
                        self.log(f"🔄 Restarting in {RESTART_COOLDOWN}s... ({self.restart_count}/{MAX_RESTARTS})")
                        time.sleep(RESTART_COOLDOWN)
                    else:
                        self.log("❌ Not restarting - giving up")
                        break
                        
            except KeyboardInterrupt:
                self.log("🛑 Ctrl+C received, shutting down...")
                self.stop()
                break
            except Exception as e:
                self.log(f"❌ Supervisor error: {e}")
                self.last_crash_time = time.time()
                self.restart_count += 1
                
                if self.should_restart():
                    self.log(f"🔄 Restarting after error in {RESTART_COOLDOWN}s...")
                    time.sleep(RESTART_COOLDOWN)
                else:
                    break
        
        self.log("🏁 Supervisor stopped")
    
    def stop(self):
        self.running = False
        if self.process and self.process.poll() is None:
            self.log("Terminating app process...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.log("Force killing app process...")
                self.process.kill()


def main():
    print("=" * 60)
    print("  Shopify Review Bot - Supervised Mode")
    print("=" * 60)
    print()
    print("  This supervisor will automatically restart the bot")
    print("  if it crashes due to EPIPE or other errors.")
    print()
    print("  Press Ctrl+C to stop.")
    print()
    print("=" * 60)
    print()
    
    runner = SupervisedRunner()
    
    # Handle SIGTERM (for production deployments)
    def signal_handler(signum, frame):
        runner.log("Received shutdown signal")
        runner.stop()
    
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        runner.run()
    except KeyboardInterrupt:
        runner.stop()


if __name__ == "__main__":
    main()
