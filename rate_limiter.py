import time
from collections import deque
from threading import Lock


class RateLimiter:
    def __init__(self, max_requests: int = 10, time_window: int = 10):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.lock = Lock()

    def wait_if_needed(self):
        with self.lock:
            now = time.time()
            
            while self.requests and self.requests[0] <= now - self.time_window:
                self.requests.popleft()
            
            if len(self.requests) >= self.max_requests:
                sleep_time = self.time_window - (now - self.requests[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self.requests.popleft()
            
            self.requests.append(time.time())

    def reset(self):
        with self.lock:
            self.requests.clear()
