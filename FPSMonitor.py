import time
from typing import List


AVG_INTERVAL_SEC = 5


class FPSMonitor:
    def __init__(self, name, printing_enabled=True):
        self.name = name
        self.ticks: List[float] = []
        self.printing_enabled = printing_enabled

    def tick(self):
        self.ticks.append(time.time())

        # Check if we have ticks spanning over more than one second
        ticks_cnt = len(self.ticks)
        if ticks_cnt > 1:
            span = self.ticks[-1] - self.ticks[0]
            if span > AVG_INTERVAL_SEC:
                current_fps = ticks_cnt / span
                if self.printing_enabled:
                    print(f"[{self.name}] - Current FPS: {current_fps}")
                self.ticks = [self.ticks[-1]]
