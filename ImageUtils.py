import cv2
import numpy as np
from typing import Tuple, Optional
from Colors import *
from Shapes import Point


def _create_hue_mask(img, lower_hue: int, upper_hue: int):
    lower = np.array([lower_hue, MIN_SATURATION, MIN_VALUE], np.uint8)
    upper = np.array([upper_hue, 255, 255], np.uint8)

    # Create a mask from the colors
    mask = cv2.inRange(img, lower, upper)
    output_img = cv2.bitwise_and(img, img, mask=mask)
    return output_img


def create_hue_masks(img, lower_hue: int, upper_hue: int):
    if upper_hue < lower_hue:  # This means we have a wrap around!
        return [
            _create_hue_mask(img, lower_hue, 179),
            _create_hue_mask(img, 0, upper_hue),
        ]

    return [_create_hue_mask(img, lower_hue, upper_hue)]


def filter_color_hsv(img, hue_lower: int, hue_upper: int):
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    hue_masks = create_hue_masks(hsv_img, hue_lower, hue_upper)

    if len(hue_masks) > 1:
        masked = cv2.addWeighted(hue_masks[0], 0.5, hue_masks[1], 0.5, 0.0)
    else:
        masked = hue_masks[0]
    grey = cv2.cvtColor(masked, cv2.COLOR_BGR2GRAY)
    return grey


def filter_cyan(img):
    return filter_color_hsv(img, CYAN_LOWER_HUE, CYAN_UPPER_HUE)


def filter_red_hsv_inverse(img):
    return filter_cyan(cv2.bitwise_not(img))


def has_min_size(c, min_size) -> bool:
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.04 * peri, True)

    if cv2.contourArea(approx) < min_size:
        return False

    return True


def dist_sq(p1: Point, p2: Point) -> int:
    return (p1.x - p2.x) * (p1.x - p2.x) + (p1.y - p2.y) * (p1.y - p2.y)


def contour_center(cnt, canvas_stretch_factor) -> Point:
    c, r = cv2.minEnclosingCircle(cnt)

    # Our canvas is bigger than the img, adjust for that
    return Point(int(c[0] * canvas_stretch_factor), int(c[1] * canvas_stretch_factor))


def find_marker_position(
    img, last_pos: Optional[Point], canvas_stretch_factor: float
) -> Optional[Point]:
    filtered = filter_red_hsv_inverse(img)

    blurred = cv2.GaussianBlur(filtered, (7, 7), 2, 2)
    thresh = cv2.threshold(blurred, MIN_VISIBLE_THRESH, 255, cv2.THRESH_BINARY)[1]
    cnts, _ = cv2.findContours(
        thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )[-2:]

    # # Debug mode: (WARNING: Will trigger epilepsy. Use at your own risk)
    # from ScreenUtils import show_img_fullscreen
    # show_img_fullscreen(thresh)
    # cv2.waitKey(50)

    points = [contour_center(cnt, canvas_stretch_factor) for cnt in cnts]
    if not points:
        return None

    if not last_pos:
        # We'll just have to guess in this case
        return points[0]

    last_pos_point = last_pos

    # If we have a few findings, filter to the one closest to the last dot
    return min(points, key=lambda x: dist_sq(x, last_pos_point))
