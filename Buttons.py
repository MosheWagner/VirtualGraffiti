import cv2
from typing import Callable, Optional
from Shapes import Point, Rectangle
from Colors import WHITE


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

    def is_pressing(self, marker_pos: Optional[Point]):
        return self.position.contains(marker_pos)

    def try_click(self, marker_pos: Optional[Point]):
        if self.is_pressing(marker_pos):
            self.callback()
            return True
        return False

    def draw(self, canvas):
        canvas[
            self.position.bottom_y() : self.position.top_y(),
            self.position.left_x() : self.position.right_x(),
        ] = self.img
