import cv2
from typing import Optional
from threading import Thread, Lock
from Shapes import Rectangle

DEF_CAMERA_ID = 0
ANDROID_VIDEO_URL = "http://10.0.0.2:8080/video"


def get_cam(video_url: Optional[str] = None, camera_id: Optional[int] = None):
    return WebcamVideoStream(video_url, camera_id).start()


def get_image(cam, crop_rect: Rectangle = None):
    img = cam.read()
    if not crop_rect:
        return img

    # Slicing requires the format of img[y:y+h, x:x+w, :]
    cropped = img[
        crop_rect.bottom_y() : crop_rect.top_y(),
        crop_rect.left_x() : crop_rect.right_x(),
        :,
    ]

    return cropped


# Based on https://gist.github.com/allskyee/7749b9318e914ca45eb0a1000a81bf56
class WebcamVideoStream:
    def __init__(self, video_url: Optional[str], camera_id: Optional[int]):
        self.stream = cv2.VideoCapture(video_url or camera_id)

        self.grabbed, self.frame = self.stream.read()
        self.started = False
        self.thread = None
        self.read_lock = Lock()

    def start(self):
        if self.started:
            # This can only be started once
            return None
        self.started = True
        self.thread = Thread(target=self.update, args=())
        self.thread.start()
        return self

    def update(self):
        while self.started:
            grabbed, frame = self.stream.read()
            self.read_lock.acquire()
            self.grabbed, self.frame = grabbed, frame
            self.read_lock.release()

    def read(self):
        self.read_lock.acquire()
        frame = self.frame.copy()
        self.read_lock.release()
        return frame

    def stop(self):
        self.started = False
        if self.thread.is_alive():
            self.thread.join()

    def __exit__(self, exc_type, exc_value, traceback):
        self.stream.release()
