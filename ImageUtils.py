import cv2
import numpy as np

from Colors import BGR_COLOR_THRESH, RED_LOWER_HUE, RED_UPPER_HUE, MIN_SATURATION, MIN_VALUE, MIN_VISIBLE_THRESH


def filter_color_bgr(img, color, thresh=BGR_COLOR_THRESH):
    # create NumPy arrays from the boundaries
    lower = np.array([max(0, c - thresh) for c in color], dtype="uint8")
    upper = np.array([min(255, c + thresh) for c in color], dtype="uint8")

    # find the colors within the specified boundaries and apply the mask
    mask = cv2.inRange(img, lower, upper)
    output = cv2.bitwise_and(img, img, mask=mask)
    gray = cv2.cvtColor(output, cv2.COLOR_BGR2GRAY)

    return gray


def _create_hue_mask(image, lower_hue, upper_hue):
    lower = np.array([lower_hue, MIN_SATURATION, MIN_VALUE], np.uint8)
    upper = np.array([upper_hue, 255, 255], np.uint8)

    # Create a mask from the colors
    mask = cv2.inRange(image, lower, upper)
    output_image = cv2.bitwise_and(image, image, mask=mask)
    return output_image


def create_hue_masks(image, lower_hue, upper_hue):
    if upper_hue < lower_hue:  # This means we have a wrap around!
        return [_create_hue_mask(image, lower_hue, 179), _create_hue_mask(image, 0, upper_hue)]

    return [_create_hue_mask(image, lower_hue, upper_hue) * 2]


def filter_color_hsv(img, hue_lower, hue_upper):
    hsv_image = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    hue_masks = create_hue_masks(hsv_image, hue_lower, hue_upper)

    full_image = cv2.addWeighted(hue_masks[0], 0.5, hue_masks[1],  0.5, 0.0)
    grey = cv2.cvtColor(full_image, cv2.COLOR_BGR2GRAY)
    return grey


def filter_red_hsv(img):
    return filter_color_hsv(img, RED_LOWER_HUE, RED_UPPER_HUE)


def is_close(n1, n2, thresh=0.05, min_diff=1):
    if abs(n1 - n2) < min_diff:
        return True
    return abs(n1 - n2) / float(n1) < thresh and abs(n1 - n2) / float(n2) < thresh


def is_square(c, min_corner_size):
    # A few quick heuristics to check if it's actually a square:
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.04 * peri, True)

    if len(approx) != 4:
        return False

    (x, y, w, h) = cv2.boundingRect(approx)
    ar = w / float(h)

    if not is_close(ar, 1):
        return False

    if cv2.contourArea(approx) < min_corner_size:
        return False

    return True


def dist_sq(p1, p2):
    return (p1[0]-p2[0])*(p1[0]-p2[0]) + (p1[1]-p2[1])*(p1[1]-p2[1])


def contour_center(cnt, canvas_stretch_factor):
    c, r = cv2.minEnclosingCircle(cnt)

    # Our canvas is bigger than the image, adjust for that
    return int(c[0]) * canvas_stretch_factor, int(c[1]) * canvas_stretch_factor


def find_marker_position(img, last_pos, canvas_stretch_factor):
    filtered = filter_red_hsv(img)

    blurred = cv2.GaussianBlur(filtered, (9, 9), 2, 2)
    thresh = cv2.threshold(blurred, MIN_VISIBLE_THRESH, 255, cv2.THRESH_BINARY)[1]
    _, cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # # Debug mode: (WARNING: Will trigger epilepsy)
    # from ScreenUtils import show_image_fullscreen
    # show_image_fullscreen(thresh)
    # cv2.waitKey(50)

    points = [contour_center(cnt, canvas_stretch_factor) for cnt in cnts]
    if not points:
        return None

    if not last_pos:
        # We'll just have to guess in this case
        return points[0]

    # If we have a few findings, filter to the one closest to the last dot
    return min(points, key=lambda x: dist_sq(x, last_pos))
