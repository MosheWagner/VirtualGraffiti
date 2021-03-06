import os
import cv2
import ctypes
import numpy as np
from typing import Tuple, Optional
from ImageUtils import (
    has_min_size,
    filter_cyan,
)
from Colors import *
from Shapes import Point, Rectangle

SQUARE_COLOR = CYAN

MIN_SCREEN_AREA = 8000

gScreenSize = None


def get_screen_size() -> Tuple[int, int]:
    global gScreenSize
    if gScreenSize is None:
        if os.name != "nt":
            raise Exception("Auto screen size only supported on windows for now!")

        user32 = ctypes.windll.user32  # type:ignore
        # TODO: If you are using 2 screens, make sure this returns the correct
        # value
        gScreenSize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    return gScreenSize[0], gScreenSize[1]


def init_display_window():
    cv2.namedWindow("IMG", cv2.WND_PROP_FULLSCREEN)  # Create a named window
    # When displaying on a different monitor, use this offset to push it to
    # there
    cv2.moveWindow("IMG", 0, 0)
    cv2.setWindowProperty("IMG", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)


def show_image_fullscreen(img, mirror=False):
    if mirror:
        img = cv2.flip(img.copy(), 1)

    h = img.shape[0]
    w = img.shape[1]
    sw, sh = get_screen_size()
    wf, hf = sw / float(w), sh / float(h)

    # Resize image to screen size; INTER_NEAREST Seems like the fastest
    # interpolation
    fs_img = cv2.resize(img, (0, 0), fx=wf, fy=hf, interpolation=cv2.INTER_NEAREST)

    cv2.imshow("IMG", fs_img)


def find_corners(filtered_img) -> Optional[Tuple[Point, Point]]:
    blurred = cv2.GaussianBlur(filtered_img, (5, 5), 0)
    thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY)[1]
    cnts, _ = cv2.findContours(
        thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )[-2:]

    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        # draw a rectangle to visualize the bounding rect
        cv2.rectangle(thresh, (x, y), (x + w, y + h), RED, 2)

    show_image_fullscreen(thresh)
    cv2.waitKey(500)

    cnts = [c for c in cnts if has_min_size(c, MIN_SCREEN_AREA)]

    if len(cnts) != 1:
        return None

    screen_rect = cnts[0]

    ext_left = min(
        tuple(screen_rect[screen_rect[:, :, 0].argmin()][0]),
        tuple(screen_rect[screen_rect[:, :, 0].argmin()][0]),
    )
    ext_right = max(
        tuple(screen_rect[screen_rect[:, :, 0].argmax()][0]),
        tuple(screen_rect[screen_rect[:, :, 0].argmax()][0]),
    )
    ext_bottom = min(
        tuple(screen_rect[screen_rect[:, :, 1].argmin()][0]),
        tuple(screen_rect[screen_rect[:, :, 1].argmin()][0]),
    )
    ext_top = max(
        tuple(screen_rect[screen_rect[:, :, 1].argmax()][0]),
        tuple(screen_rect[screen_rect[:, :, 1].argmax()][0]),
    )

    return Point(ext_left[0], ext_bottom[1]), Point(ext_right[0], ext_top[1])


def calibrate_screen_bounds(cam) -> Optional[Rectangle]:
    img = cam.read()
    h, w, _ = img.shape

    cnvs = np.zeros(img.shape, np.uint8)

    cv2.rectangle(cnvs, (0, 0), (w, h), SQUARE_COLOR, cv2.FILLED)

    corners = None
    for _ in range(5):
        show_image_fullscreen(cnvs)

        cv2.waitKey(1000)

        img = cam.read()
        filtered = filter_cyan(img)

        corners = find_corners(filtered)
        cv2.waitKey(1000)

        if corners:
            break
    else:
        print("Failed to find screen corners!")
        return None

    # print ("Corners are at: ", corners)

    return Rectangle(*corners)
