import contextlib
import tempfile
from pathlib import Path
import time

class FileLock:
    """Cross-platform file locking implementation."""
    
    def __init__(self, path: Path):
        self.lock_path = path.with_suffix('.lock')
        self.timeout = 60  # Maximum wait time in seconds
        
    @contextlib.contextmanager
    def acquire(self):
        start_time = time.time()
        while True:
            try:
                # Try to create the lock file
                with open(self.lock_path, 'x') as f:
                    try:
                        yield
                        return
                    finally:
                        # Remove the lock file in finally block
                        self.lock_path.unlink(missing_ok=True)
            except FileExistsError:
                if time.time() - start_time > self.timeout:
                    raise TimeoutError("Could not acquire lock")
                time.sleep(0.1)  # Short sleep before retry