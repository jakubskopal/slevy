import os
import sys
import shutil
import time
import threading
from datetime import datetime, timedelta

class Console:
    def __init__(self, total=0, use_colors=True):
        self.total = total
        self.current = 0
        self.use_colors = use_colors
        self.start_time = None
        self.last_update_time = 0
        self.last_stats = ""
        self.bar_update_interval = 1.0  # Update max once per second for both modes
        self._lock = threading.Lock()

    def increment(self, amount=1):
        with self._lock:
            self.current += amount
            if self.use_colors:
                self._draw_bar_unlocked()
    
    def set_total(self, total):
        with self._lock:
            self.total = total

    def start(self):
        with self._lock:
            self.start_time = time.time()
            self.last_update_time = 0

    def log(self, msg, notice=False):
        with self._lock:
            if os.environ.get("GITHUB_ACTIONS") and notice:
                 clean_msg = msg.replace('\n', ' ').strip()
                 print(f"::notice::{clean_msg}", flush=True)

            if self.use_colors:
                # Clear line, print msg, redraw bar
                sys.stdout.write("\r\033[K")
                sys.stdout.write(f"{msg}\n")
                self._draw_bar_unlocked(force=True)
            else:
                # Simple logging
                print(msg)

    def update(self, current, stats="", force=False):
        with self._lock:
            self.current = current
            self.last_stats = stats
            if self.use_colors:
                self._draw_bar_unlocked(force=force)

    def _draw_bar_unlocked(self, force=False):
        now = time.time()
        if not force and (now - self.last_update_time < self.bar_update_interval):
            return

        self.last_update_time = now
        
        # Calculate ETA
        eta_str = "??"
        if self.start_time and self.current > 0:
            elapsed = now - self.start_time
            rate = self.current / elapsed
            if rate > 0:
                remaining_items = max(0, self.total - self.current)
                eta_seconds = remaining_items / rate
                eta_str = str(timedelta(seconds=int(eta_seconds)))

        fraction = self.current / self.total if self.total > 0 else 0
        fraction = min(1.0, max(0.0, fraction)) # clamp
        
        if self.use_colors:
            # Get terminal width
            columns, _ = shutil.get_terminal_size(fallback=(80, 24))
            
            # Format: [====      ] 123/8500 | Stats... | ETA: 0:00:12
            progress = f" {self.current}/{self.total}"
            eta = f" | ETA: {eta_str}"
            stats = f" | {self.last_stats}" if self.last_stats else ""
            
            info = f"{progress}{stats}{eta}"
            info_len = len(info)
            
            # [ + bar + ] + info
            # Bar needs at least small width, say 10 chars
            # Subtract 1 from columns to avoid edge-case wrapping/leaking
            available_width = (columns - 1) - info_len - 2 # -2 for brackets []
            
            if available_width < 10:
                # If too narrow, just print info without bar (or truncated)
                 sys.stdout.write(f"\r\033[K{info}")
            else:
                filled = int(fraction * available_width)
                bar_graph = "=" * filled + " " * (available_width - filled)
                
                # \r to start, \033[K to clear line
                # Dark gray brackets, Green bar, Reset
                sys.stdout.write(f"\r\033[K\033[90m[\033[32m{bar_graph}\033[90m]\033[0m{info}")
            
            sys.stdout.flush()
        
        else:
            # Simple Output Mode
            # Progress: 45% (3800/8500) | Stats... | ETA: 0:02:15
            pct = int(fraction * 100)
            stats = f" | {self.last_stats}" if self.last_stats else ""
            
            line = f"Progress: {pct}% ({self.current}/{self.total}){stats} | ETA: {eta_str}"
            sys.stdout.write(f"{line}\n")
            sys.stdout.flush()

    def finish(self):
        with self._lock:
            if self.use_colors:
                sys.stdout.write("\n")
                sys.stdout.flush()
            else:
                sys.stdout.write("Done.\n")
                sys.stdout.flush()
