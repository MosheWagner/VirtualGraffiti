"""Laser Graffiti game.

Example usage with Android camera (using IP camera app):
$ python Graffiti.py --video_url="http://10.0.0.3:8080/video" --canvas_size=500,1000
"""


import cv2
import numpy as np
import argparse
import datetime
from typing import Tuple, Optional, List, Callable
from ImageUtils import find_marker_position, dist_sq
from ScreenUtils import show_image_fullscreen, calibrate_screen_bounds
from CamUtils import get_image, get_cam
from Colors import *
from Shapes import Point, Rectangle
from Buttons import Button

parser = argparse.ArgumentParser(description="Laser Graffiti game")


def int_pair(arg) -> List[int]:
    if len(arg.split(",")) != 2:
        raise argparse.ArgumentError
    return [int(x) for x in arg.split(",")]


parser.add_argument(
    "--video_url",
    default=None,
    type=str,
    help="Path to video feed (use for external camera feed)",
)

parser.add_argument(
    "--cemera_id",
    default=None,
    type=str,
    help="System id of the camera, starting from 0 (set when using device's camera)",
)

parser.add_argument(
    "--canvas_size",
    default="600,1200",
    type=int_pair,
    help="Requested size of canvas, in tuple form h,w. The actual canvas shape (and thus size) will depend on the detected screen's shape",
)


TICK_MS = 20
CLEAR_MS = TICK_MS * 2
BASE_RADIUS = 2
GAP_DIST = TICK_MS * 15

MAX_SNAPS_PER_FRAME = 4
BUTTON_SIZE = 100

SHOW_MARKER = True

color_code_map = {
    "W": WHITE,
    "B": BLUE,
    "G": GREEN,
    "Y": YELLOW,
}


class GraffitiState:
    canvas_size: Tuple[int, int]
    img_channels: int
    canvas_stretch_factor: float
    radius: int
    last_dot: Optional[Point]
    clear_cnt: int
    max_gap_dist_sq: int
    buttons: List[Button]
    quit: bool

    def __init__(
        self,
        canvas_size: Tuple[int, int],
        img_channels: int,
        canvas_stretch_factor: float,
    ):
        self.canvas_size = canvas_size
        self.img_channels = img_channels
        self.canvas_stretch_factor = canvas_stretch_factor
        max_gap_dist = int(GAP_DIST * canvas_stretch_factor)
        self.max_gap_dist_sq = max_gap_dist * max_gap_dist
        self.quit = False
        self.clear()
        self.buttons = []
        self.next_button_x = self.canvas_size[1] - BUTTON_SIZE
        self.next_button_y = 0
        self.add_button(self.clear, "Icons/Clear.png")
        self.add_button(self.set_quit, "Icons/Exit.png")

    def add_button(self, callback: Callable, icon_path: str):
        button = Button(
            callback,
            Rectangle(
                Point(self.next_button_x, self.next_button_y),
                Point(
                    self.next_button_x + BUTTON_SIZE, self.next_button_y + BUTTON_SIZE
                ),
            ),
            icon_path,
        )
        self.buttons.append(button)
        self.next_button_y += int(BUTTON_SIZE * 1.5)

    def clear_canvas(self):
        self.canvas = gen_blank_canvas(self.canvas_size, self.img_channels)

    def clear(self):
        self.clear_canvas()
        self.last_dot = None
        self.color = GREEN
        self.radius = BASE_RADIUS
        self.clear_cnt = 0

    def inc_radius(self):
        self.radius += 1

    def dec_radius(self):
        self.radius -= 1
        self.radius = max(1, self.radius)

    def set_color(self, color_code_char):
        if color_code_char not in color_code_map:
            return
        self.color = color_code_map[color_code_char]

    def set_quit(self):
        self.quit = True


def get_key_press(wait_ms: int) -> Optional[str]:
    key_code = cv2.waitKey(wait_ms)
    try:
        key = chr(key_code)
    except ValueError:
        return None

    return key.upper()


def gen_blank_canvas(canvas_size: Tuple[int, int], img_channels: int):
    return np.zeros(
        (
            canvas_size[0],
            canvas_size[1],
            img_channels,
        ),
        np.uint8,
    )


def calculate_canvas_size_and_stretch(
    bounds: Rectangle, rquested_canvas_size: Tuple[int, int]
) -> Tuple[Tuple[int, int], float]:
    canvas_stretch_factor_h = rquested_canvas_size[0] / bounds.width()
    canvas_stretch_factor_w = rquested_canvas_size[1] / bounds.height()

    canvas_stretch_factor = (canvas_stretch_factor_w + canvas_stretch_factor_h) / 2
    canvas_size = int(bounds.height() * canvas_stretch_factor), int(
        bounds.width() * canvas_stretch_factor
    )

    print(canvas_size)
    return canvas_size, canvas_stretch_factor


def do_graffiti(
    cam,
    bounds: Rectangle,
    rquested_canvas_size: Tuple[int, int],
    mirror: bool = False,
):
    img = get_image(cam, bounds)

    canvas_size, canvas_stretch_factor = calculate_canvas_size_and_stretch(
        bounds, rquested_canvas_size
    )
    img_channels = img.shape[2]

    state = GraffitiState(canvas_size, img_channels, canvas_stretch_factor)

    game_loop(cam, bounds, mirror, state)


def draw_graffiti(state: GraffitiState, marker_position: Optional[Point]):
    if marker_position:
        if state.last_dot:
            # Draw a line from the last position to ours
            if dist_sq(state.last_dot, marker_position) < state.max_gap_dist_sq:
                cv2.line(
                    state.canvas,
                    state.last_dot.as_tuple(),
                    marker_position.as_tuple(),
                    state.color,
                    thickness=state.radius,
                    lineType=cv2.LINE_AA,
                )
        state.last_dot = marker_position
    else:
        state.clear_cnt += 1

        if state.clear_cnt > CLEAR_MS / TICK_MS:
            state.clear_cnt = 0
            state.last_dot = None


def game_loop(
    cam,
    bounds: Rectangle,
    mirror: bool,
    state: GraffitiState,
):
    # Clear screen
    show_image_fullscreen(state.canvas)
    cv2.waitKey(50)

    while True:
        loop_start = datetime.datetime.now()

        # Find marker position
        for i in range(MAX_SNAPS_PER_FRAME):
            img = get_image(cam, bounds)
            marker_position = find_marker_position(
                img, state.last_dot, state.canvas_stretch_factor
            )
            if marker_position:
                break

        for btn in state.buttons:
            btn.try_click(marker_position)

        if state.quit:
            return

        draw_graffiti(state, marker_position)

        draw = state.canvas.copy()
        if marker_position and SHOW_MARKER:
            cv2.circle(draw, marker_position.as_tuple(), 5, BLUE, 2)

        for bnt in state.buttons:
            bnt.draw(draw)

        show_image_fullscreen(draw, mirror)

        loop_end = datetime.datetime.now()
        delta = loop_end - loop_start
        delta_ms = int(delta.total_seconds() * 1000)
        sleep_millis = max(5, TICK_MS - delta_ms)

        k = get_key_press(sleep_millis)

        # Keyboard meta commands
        if k == "C":
            # Clear command
            state.clear()
        if k in color_code_map:
            # Color change command
            state.set_color(k)
        elif k == "[":
            state.inc_radius()
        elif k == "]":
            state.dec_radius()
        elif k == "S" or k == "Q":
            # Quit
            return


def main():
    args = parser.parse_args()

    cam_stream = get_cam(video_url=args.video_url, camera_id=args.cemera_id)
    try:
        bounds = calibrate_screen_bounds(cam_stream)

        if not bounds:
            cam_stream.stop()
            return

        do_graffiti(cam_stream, bounds, args.canvas_size)
    finally:
        cam_stream.stop()


if __name__ == "__main__":
    main()
