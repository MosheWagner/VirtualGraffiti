"""Laser Graffiti game.

Example usage with Android camera (using IP camera app):
$ python Graffiti.py --video_url="http://10.0.0.3:8080/video"
"""


import cv2
import numpy as np
import argparse
import datetime
from typing import Tuple
from ImageUtils import find_marker_position, dist_sq
from ScreenUtils import show_image_fullscreen, calibrate_screen_bounds
from CamUtils import get_image, get_cam
from Colors import *


parser = argparse.ArgumentParser(description="Laser Graffiti game")


def int_pair(arg):
    if len(arg.split(",")) != 2:
        raise argparse.ArgumentError(
            "Must use a pair of integers seperated with a comma!"
        )
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
    help="System id of the camera, starting from 0 (when using device's camera)",
)

parser.add_argument(
    "--canvas_size",
    default="500,1000",
    type=int_pair,
    help="Requested size of canvas, in tuple form h,w. The exact canvas shape (and thus size) will depend on the detected screen's shape",
)


TICK_MS = 20
CLEAR_MS = TICK_MS * 2
BASE_RADIUS = 2
GAP_DIST = TICK_MS * 15

MAX_SNAPS_PER_FRAME = 4

SHOW_MARKER = True

color_code_map = {
    "W": WHITE,
    "B": BLUE,
    "G": GREEN,
    "Y": YELLOW,
}


class GraffitiState:
    def __init__(self):
        self.radius = BASE_RADIUS
        self.color = GREEN
        self.last_dot = None
        self.clear_cnt = 0


def get_key_press(wait_ms):
    key_code = cv2.waitKey(wait_ms)
    try:
        key = chr(key_code)
    except ValueError:
        return None

    return key.upper()


def blank_canvas(canvas_size: Tuple[int, int], channels: int):
    return np.zeros(
        (
            canvas_size[0],
            canvas_size[1],
            channels,
        ),
        np.uint8,
    )


def do_graffiti(
    cam,
    bounds: Tuple[int, int, int, int],
    rquested_canvas_size: Tuple[int, int],
    mirror: bool = False,
):
    img = get_image(cam, bounds)

    bounds_size_y = bounds[3] - bounds[2]
    bounds_size_x = bounds[1] - bounds[0]
    canvas_stretch_factor_h = rquested_canvas_size[0] / bounds_size_y
    canvas_stretch_factor_w = rquested_canvas_size[1] / bounds_size_x

    canvas_stretch_factor = (canvas_stretch_factor_w + canvas_stretch_factor_h) / 2
    canvas_size = int(bounds_size_y * canvas_stretch_factor), int(
        bounds_size_x * canvas_stretch_factor
    )
    channels = img.shape[2]

    gap_dist = GAP_DIST * canvas_stretch_factor

    state = GraffitiState()
    canvas = blank_canvas(canvas_size, channels)
    radius = BASE_RADIUS
    color = GREEN
    last_dot = None
    clear_cnt = 0

    # Clear screen
    show_image_fullscreen(canvas)
    cv2.waitKey(50)

    while True:
        loop_start = datetime.datetime.now()
        for i in range(MAX_SNAPS_PER_FRAME):
            img = get_image(cam, bounds)
            marker_position = find_marker_position(img, last_dot, canvas_stretch_factor)
            if marker_position:
                break

        if marker_position:
            cx, cy = marker_position

            if last_dot:
                # Draw a line from the last position to ours
                if dist_sq(last_dot, (cx, cy)) < gap_dist * gap_dist:
                    cv2.line(
                        canvas,
                        last_dot,
                        (cx, cy),
                        color,
                        thickness=radius,
                        lineType=cv2.LINE_AA,
                    )
            last_dot = (cx, cy)
        else:
            clear_cnt += 1

            if clear_cnt > CLEAR_MS / TICK_MS:
                clear_cnt = 0
                last_dot = None

        draw = canvas.copy()
        if marker_position and SHOW_MARKER:
            cv2.circle(draw, marker_position, 5, BLUE, 2)

        show_image_fullscreen(draw, mirror)

        loop_end = datetime.datetime.now()
        delta = loop_end - loop_start
        delta_ms = int(delta.total_seconds() * 1000)
        sleep_millis = max(5, TICK_MS - delta_ms)
        k = get_key_press(sleep_millis)

        if k == "C":
            # Clear command
            last_dot = None
            canvas = blank_canvas(canvas_size, channels)
            radius = BASE_RADIUS  # Back to normal size
        if k in color_code_map:
            # Color change command
            color = color_code_map[k]
        elif k == "[" or k == "]":
            # Cursor size change command
            radius += 1 if k == "[" else -1
            radius = max(1, radius)
        elif k == "S" or k == "Q":
            return


def main():
    args = parser.parse_args()

    cam_stream = get_cam(video_url=args.video_url, camera_id=args.cemera_id)
    bounds = calibrate_screen_bounds(cam_stream)

    if not bounds:
        cam_stream.stop()
        return

    try:
        do_graffiti(cam_stream, bounds, args.canvas_size)
    except Exception as e:
        cam_stream.stop()
        raise e

    cam_stream.stop()


if __name__ == "__main__":
    main()
