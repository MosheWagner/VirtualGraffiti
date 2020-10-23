"""Laser Graffiti game.

Example usage with Android camera (using IP camera app):
$ python Graffiti.py --video_url="http://10.0.0.3:8080/video"
"""


import cv2
import numpy as np
import argparse
import datetime

from ImageUtils import find_marker_position, dist_sq
from ScreenUtils import show_image_fullscreen, calibrate_screen_bounds
from CamUtils import get_image, get_cam
from Colors import *


parser = argparse.ArgumentParser(description='Laser Graffiti game')
parser.add_argument('--video_url', default=None, type=str,
                   help='Path to video feed (use for external camera feed)')
                   
parser.add_argument('--cemera_id', default=None, type=str,
                   help="System id of the camera, starting from 0 (when using device's camera)")
                   

TICK_MS = 20
CLEAR_MS = TICK_MS * 2
BASE_RADIUS = 2
# TODO: Use fixed canvas size instead, which will define the STRETCH factor
CANVAS_STRETCH = 3
GAP_DIST = TICK_MS * 15 * CANVAS_STRETCH

MAX_SNAPS_PER_FRAME = 4

SHOW_MARKER = True

color_code_map = {
    'W': WHITE,
    'B': BLUE,
    'G': GREEN,
    'Y': YELLOW,
}


class GraffitiState():
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


def do_graffiti(cam, bounds, mirror=False):
    img = get_image(cam, bounds)

    state = GraffitiState()
    canvas = np.zeros((img.shape[0]*CANVAS_STRETCH, img.shape[1]*CANVAS_STRETCH, img.shape[2]), np.uint8)
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
            marker_position = find_marker_position(img, last_dot, CANVAS_STRETCH)
            if marker_position:
                break
        
        if marker_position:
            cx, cy = marker_position
            
            if last_dot:
                # Draw a line from the last position to ours
                if dist_sq(last_dot, (cx, cy)) < GAP_DIST*GAP_DIST:
                    cv2.line(canvas, last_dot, (cx, cy), color, thickness=radius, lineType=cv2.LINE_AA)
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
        elif k == 'S' or k == 'Q':
            return
                     

def main():
    args = parser.parse_args()
    
    cam_stream = get_cam(video_url=args.video_url, camera_id=args.cemera_id)
    bounds = calibrate_screen_bounds(cam_stream)
    if not bounds:
        cam_stream.stop()
        return 

    try:
        do_graffiti(cam_stream, bounds)
    except Exception as e: 
        cam_stream.stop()
        raise e

    cam_stream.stop()


if __name__ == '__main__':
    main()
