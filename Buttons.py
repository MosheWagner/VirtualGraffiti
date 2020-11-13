import cv2
from typing import Callable, Optional
from Shapes import Point, Rectangle
from Colors import WHITE
import numpy as np


class Button:
    # callback: Callable
    position: Rectangle

    def __init__(
        self,
        callback: Callable,
        position: Rectangle,
        image_path: str,
        frame_color=WHITE,
    ):
        self.callback = callback
        self.position = position
        self.img = cv2.resize(
            cv2.imread(image_path),
            (self.position.width(), self.position.height()),
            interpolation=cv2.INTER_AREA,
        )

        # Draw frame
        cv2.line(
            self.img,
            (0, 0),
            (0, self.position.top_y()),
            frame_color,
            thickness=2,
            lineType=cv2.LINE_AA,
        )
        cv2.line(
            self.img,
            (0, 0),
            (self.position.right_x(), 0),
            frame_color,
            thickness=2,
            lineType=cv2.LINE_AA,
        )
        cv2.line(
            self.img,
            (self.position.right_x() - 2, self.position.top_y() - 2),
            (self.position.right_x() - 2, 2),
            frame_color,
            thickness=2,
            lineType=cv2.LINE_AA,
        )
        cv2.line(
            self.img,
            (self.position.right_x() - 2, self.position.top_y() - 2),
            (2, self.position.top_y() - 2),
            frame_color,
            thickness=2,
            lineType=cv2.LINE_AA,
        )

    def is_pressed(self, marker_pos: Optional[Point]):
        return self.position.contains(marker_pos)

    def do_callback(self):
        self.callback()

    def draw(self, canvas, marker_pos: Optional[Point]):
        if marker_pos and self.is_pressed(marker_pos):
            canvas[
                self.position.bottom_y() : self.position.top_y(),
                self.position.left_x() : self.position.right_x(),
            ] = np.zeros(
                self.img.shape,
                np.uint8,
            )
        else:
            canvas[
                self.position.bottom_y() : self.position.top_y(),
                self.position.left_x() : self.position.right_x(),
            ] = self.img
