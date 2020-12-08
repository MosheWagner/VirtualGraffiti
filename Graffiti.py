"""Laser Graffiti game.

Example usage with Android camera (using IP camera app):
$ python Graffiti.py --video_url="http://10.0.0.3:8080/video"
"""


import cv2
import numpy as np
import time
import argparse
import datetime
from typing import Tuple, Optional, List, Callable
from ImageUtils import find_marker_position_t, dist_sq, save_img_with_ts
from ScreenUtils import (
    show_image_fullscreen,
    calibrate_screen_bounds,
    get_screen_size,
    init_display_window,
)
from CamUtils import get_cam
from Colors import *
from Shapes import Point, Rectangle
from Buttons import Button
from FPSMonitor import FPSMonitor
from Timestamper import Timestamper
from multiprocessing import Pool

# Performance TODOs:

# FPS issues:
# 1. Marker finding (15ms, done in multiple processes).
# 2. Image show ("waitKey", 10-20ms)

# Latency:
# 1. Camera latency (??)
# 2. Camera image crop and copy (40ms!)
# 3. Marker finding (15ms)
# 4. Image show ("waitKey", 40ms)


parser = argparse.ArgumentParser(description="Laser Graffiti game")

parser.add_argument(
    "--video_url",
    default=None,
    type=str,
    help="Path to video feed (use for external camera feed)",
)

parser.add_argument(
    "--cemera_id",
    default=None,
    type=int,
    help="System id of the camera, starting from 0 (set when using device's camera)",
)

parser.add_argument(
    "--perf_prints",
    default=False,
    type=bool,
    help="Enable performance debug prints",
)

# TODO: All these consts are horrible, and mostly don't do what they should...
TICK_MS = 5
CLEAR_MS = TICK_MS
BASE_RADIUS = 2
GAP_DIST = TICK_MS * 15
BTN_CLICK_SLEEP = 100

MAX_SNAPS_PER_FRAME = 4
BUTTON_SCREEN_FRACTION = 0.07

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
        button_size = int(canvas_size[1] * BUTTON_SCREEN_FRACTION)
        self.next_button_x = self.canvas_size[1] - button_size
        self.next_button_y = 0
        self.add_button(self.clear, "Icons/Clear.png", button_size)
        self.next_button_y += button_size
        self.add_button(self.save_img, "Icons/Save.png", button_size)
        # Put the exit button as low down as possible
        self.next_button_y = self.canvas_size[0] - button_size - 10
        self.add_button(self.set_quit, "Icons/Exit.png", button_size)

    def add_button(self, callback: Callable, icon_path: str, button_size: int):
        button = Button(
            callback,
            Rectangle(
                Point(self.next_button_x, self.next_button_y),
                Point(
                    self.next_button_x + button_size, self.next_button_y + button_size
                ),
            ),
            icon_path,
        )
        self.buttons.append(button)
        self.next_button_y += int(button_size * 1.5)

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

    def save_img(self):
        save_img_with_ts(img=self.canvas, out_dir="SavedImages")


def get_key_press(wait_ms: int) -> Optional[str]:
    key_code = cv2.waitKey(wait_ms)
    if key_code < 0:
        return None

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

    return canvas_size, canvas_stretch_factor


def do_graffiti(
    cam,
    bounds: Rectangle,
    rquested_canvas_size: Tuple[int, int],
    mirror: bool = False,
    enable_perf_prints: bool = False,
):
    img = cam.read()

    canvas_size, canvas_stretch_factor = calculate_canvas_size_and_stretch(
        bounds, rquested_canvas_size
    )
    img_channels = img.shape[2]

    state = GraffitiState(canvas_size, img_channels, canvas_stretch_factor)

    game_loop(cam, state, mirror, enable_perf_prints)


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
    state: GraffitiState,
    mirror: bool,
    enable_perf_prints: bool,
):
    # Clear screen
    show_image_fullscreen(state.canvas)
    cv2.waitKey(50)

    process_pool = Pool()
    timestamper = Timestamper(printing_enabled=enable_perf_prints)
    fps_monitor = FPSMonitor(
        "Main loop fps monitor", printing_enabled=enable_perf_prints
    )

    while True:
        fps_monitor.tick()
        loop_start = datetime.datetime.now()

        timestamper.stamp_start("Image reading")
        params = [
            (cam.read(), state.last_dot, state.canvas_stretch_factor)
            for _ in range(MAX_SNAPS_PER_FRAME)
        ]

        timestamper.stamp_start("Marker finding")
        maybe_positions = process_pool.map(find_marker_position_t, params)
        marker_position = next(
            (pos for pos in maybe_positions if pos is not None), None
        )

        timestamper.stamp_start("Buttons")

        clicked = None
        for btn in state.buttons:
            if btn.is_pressed(marker_position):
                clicked = btn
                btn.do_callback()

        if state.quit:
            return

        timestamper.stamp_start("Drawing")

        draw_graffiti(state, marker_position)

        # Ideally we would want to copy the canvas here, but this takes unberablly long (~15ms on my laptop).
        # We avoid that and simply re-draw the buttons again and again on the original canvas.
        draw = state.canvas

        for bnt in state.buttons:
            bnt.draw(draw, marker_position)

        timestamper.stamp_start("Display")

        show_image_fullscreen(draw, mirror)

        timestamper.stamp_start("Sleep")

        loop_end = datetime.datetime.now()
        delta = loop_end - loop_start
        delta_ms = int(delta.total_seconds() * 1000)
        required_sleep_millis = TICK_MS - delta_ms

        sleep_millis = max(1, required_sleep_millis)

        if clicked:
            sleep_millis = BTN_CLICK_SLEEP

        timestamper.stamp_start("Image show")
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

    init_display_window()

    cam_stream = get_cam(
        video_url=args.video_url,
        camera_id=args.cemera_id,
        enable_perf_prints=args.perf_prints,
    )
    try:
        bounds = calibrate_screen_bounds(cam_stream)

        if not bounds:
            cam_stream.stop()
            return

        cam_stream.update_crop_rect(bounds)
        do_graffiti(
            cam=cam_stream,
            bounds=bounds,
            rquested_canvas_size=get_screen_size(),
            enable_perf_prints=args.perf_prints,
        )
    finally:
        cam_stream.stop()


if __name__ == "__main__":
    main()
