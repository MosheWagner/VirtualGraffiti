import cv2
import time
from typing import Optional
from threading import Thread, Lock
from Shapes import Rectangle
from FPSMonitor import FPSMonitor


def get_cam(
    video_url: Optional[str] = None,
    camera_id: Optional[int] = None,
    enable_perf_prints: bool = False,
):
    return WebcamVideoStream(video_url, camera_id, enable_perf_prints).start()


# Based on https://gist.github.com/allskyee/7749b9318e914ca45eb0a1000a81bf56
class WebcamVideoStream:
    def __init__(
        self,
        video_url: Optional[str],
        camera_id: Optional[int],
        enable_perf_prints: bool,
    ):
        self.stream = cv2.VideoCapture(video_url or camera_id)

        self.grabbed, self.frame = self.stream.read()
        self.running = False
        self.thread = None
        self.crop_rect: Optional[Rectangle] = None
        self.lock = Lock()
        self.fps_monitor = FPSMonitor(
            "Camera fps monitor", printing_enabled=enable_perf_prints
        )

    def update_crop_rect(self, crop_rect: Rectangle):
        self.crop_rect = crop_rect

    def start(self):
        if self.running:
            # This can only be started once
            return None
        self.running = True
        self.thread = Thread(target=self.update, args=())
        self.thread.start()
        return self

    def update(self):
        while self.running:
            self.fps_monitor.tick()
            _, frame = self.stream.read()
            crop_rect = self.crop_rect
            if crop_rect:
                frame = frame[
                    crop_rect.bottom_y() : crop_rect.top_y(),
                    crop_rect.left_x() : crop_rect.right_x(),
                    :,
                ]

            frame_copy = frame.copy()
            with self.lock:
                self.frame = frame_copy

    def read(self):
        with self.lock:
            return self.frame

    def stop(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join()

    def __exit__(self, exc_type, exc_value, traceback):
        self.stream.release()
