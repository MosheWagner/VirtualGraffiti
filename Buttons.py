import cv2
from typing import Callable, Optional
from Shapes import Point, Rectangle
from Colors import WHITE
import numpy as np


IMG_FILL_FACTOR = 0.5
BORDER_WITH = 3


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
        # Black background
        self.img = np.zeros(
            (self.position.width(), self.position.height(), 3),
            np.uint8,
        )
        pic = cv2.resize(
            cv2.imread(image_path),
            (
                int(self.position.width() * IMG_FILL_FACTOR),
                int(self.position.height() * IMG_FILL_FACTOR),
            ),
            interpolation=cv2.INTER_AREA,
        )
        full_margin_x = self.position.width() - int(
            self.position.width() * IMG_FILL_FACTOR
        )
        half_margin_x = full_margin_x // 2
        margin_x_correct = full_margin_x - (half_margin_x * 2)
        full_margin_y = self.position.height() - int(
            self.position.height() * IMG_FILL_FACTOR
        )
        half_margin_y = full_margin_y // 2
        margin_y_correct = full_margin_y - (half_margin_y * 2)
        self.img[
            half_margin_y + margin_y_correct : self.position.height() - half_margin_y,
            half_margin_x + margin_x_correct : self.position.width() - half_margin_x,
        ] = pic

        # Draw frame
        cv2.line(
            self.img,
            (0, 0),
            (0, self.position.top_y()),
            frame_color,
            thickness=BORDER_WITH,
            lineType=cv2.LINE_AA,
        )
        cv2.line(
            self.img,
            (0, 0),
            (self.position.right_x(), 0),
            frame_color,
            thickness=BORDER_WITH,
            lineType=cv2.LINE_AA,
        )
        cv2.line(
            self.img,
            (self.position.right_x(), self.position.top_y()),
            (self.position.right_x(), 0),
            frame_color,
            thickness=BORDER_WITH,
            lineType=cv2.LINE_AA,
        )
        cv2.line(
            self.img,
            (self.position.right_x(), self.position.top_y()),
            (0, self.position.top_y()),
            frame_color,
            thickness=BORDER_WITH,
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
