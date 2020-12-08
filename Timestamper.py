import time

EPSILON_SEC = 1 / 1000.0


class Timestamper:
    def __init__(self, printing_enabled=True):
        self.printing_enabled = printing_enabled
        self.last_timestamp = time.time()
        self.last_section_name = ""

    def stamp_start(self, new_section_name: str, skip_print: bool = False):
        time_delta = time.time() - self.last_timestamp
        if (
            self.printing_enabled
            and not skip_print
            and self.last_section_name
            and time_delta > EPSILON_SEC
        ):
            print(f"{self.last_section_name} - {time_delta*1000:.1f}ms")

        self.last_timestamp = time.time()
        self.last_section_name = new_section_name
