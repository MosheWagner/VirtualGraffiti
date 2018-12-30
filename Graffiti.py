import cv2
import numpy as np

from ImageUtils import find_marker_position, dist_sq
from ScreenUtils import show_image_fullscreen, calibrate_screen_bounds
from CamUtils import get_image, get_cam
from Colors import *


TICK_MS = 50
CLEAR_MS = 100
BASE_RADIUS = 2
CANVAS_STRETCH = 3
GAP_DIST = 100 * CANVAS_STRETCH


color_code_map = {
    'W': WHITE,
    'B': BLUE,
    'G': GREEN,
    'Y': YELLOW,
}


def get_key_press(wait_ms):
    key_code = cv2.waitKey(wait_ms)
    try:
        key = chr(key_code)
    except ValueError:
        return None

    return key.upper()


def do_graffiti(cam, bounds, mirror=False):
    img = get_image(cam, bounds)

    canvas = np.zeros((img.shape[0]*CANVAS_STRETCH, img.shape[1]*CANVAS_STRETCH, img.shape[2]), np.uint8)
    radius = BASE_RADIUS
    color = GREEN
    last_dot = None
    clear_cnt = 0
    
    show_image_fullscreen(canvas)
    cv2.waitKey(50)
    
    while True:
        img = get_image(cam, bounds)

        marker_position = find_marker_position(img, last_dot, CANVAS_STRETCH)
        if marker_position:
            cx, cy = marker_position
            if last_dot:
                # draw a line from the last position to ours
                if dist_sq(last_dot, (cx, cy)) < GAP_DIST*GAP_DIST:
                    cv2.line(canvas, last_dot, (cx, cy), color, thickness=radius, lineType=cv2.LINE_AA)
            last_dot = (cx, cy)
        else:
            clear_cnt += 1

            if clear_cnt > CLEAR_MS / TICK_MS:
                clear_cnt = 0
                last_dot = None

        show_image_fullscreen(canvas, mirror)

        k = get_key_press(TICK_MS)

        if k == 'C':
            # Clear command
            last_dot = None
            canvas = np.zeros((img.shape[0]*CANVAS_STRETCH, img.shape[1]*CANVAS_STRETCH, img.shape[2]), np.uint8)
            radius = BASE_RADIUS  # Back to normal size
        if k in color_code_map:
            # Color change command
            color = color_code_map[k]
        elif k == '[' or k == ']':
            # Cursor size change command
            radius += 1 if k == '[' else -1
            radius = max(1, radius)


def main():
    cam = get_cam()
    bounds = calibrate_screen_bounds(cam)

    do_graffiti(cam, bounds)


if __name__ == '__main__':
    main()
