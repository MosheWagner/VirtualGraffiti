import os
import cv2
import ctypes
import numpy as np


from CamUtils import get_image
from ImageUtils import is_square, filter_color_bgr
from Colors import WHITE, RED


MIN_SCREEN_CORNER_SIZE = 100

gScreenSize = None


def get_screen_size():
    global gScreenSize
    if gScreenSize is None:
        if os.name != 'nt':
            raise Exception('Auto screen size only supported on windows for now!')

        user32 = ctypes.windll.user32
        # TODO: If you are using 2 screens, make sure this returns the correct value

        gScreenSize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    return gScreenSize[0], gScreenSize[1]


def show_image_fullscreen(img, mirror=False):
    if mirror:
        img = cv2.flip(img.copy(), 1)

    h = img.shape[0]
    w = img.shape[1]
    sw, sh = get_screen_size()
    wf, hf = sw / float(w), sh / float(h)

    # Resize image to screen size

    fs_img = cv2.resize(img, (0, 0), fx=wf, fy=hf)

    cv2.namedWindow("IMG", cv2.WND_PROP_FULLSCREEN)  # Create a named window
    cv2.moveWindow("IMG", 0, 0)  # When displaying on a different monitor, use this offset to push it to there
    cv2.setWindowProperty("IMG", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.imshow("IMG", fs_img)


def find_corners(img):
    # Filter our all but white
    filtered = filter_color_bgr(img, WHITE)

    blurred = cv2.GaussianBlur(filtered, (5, 5), 0)
    thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)[1]
    _, cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        # draw a rectangle to visualize the bounding rect
        cv2.rectangle(img, (x, y), (x + w, y + h), RED, 2)

    show_image_fullscreen(img)
    cv2.waitKey(500)

    cnts = [c for c in cnts if is_square(c, MIN_SCREEN_CORNER_SIZE)]

    if len(cnts) != 2:
        return None

    ext_left = min(tuple(cnts[0][cnts[0][:, :, 0].argmin()][0]), tuple(cnts[1][cnts[1][:, :, 0].argmin()][0]))
    ext_right = max(tuple(cnts[0][cnts[0][:, :, 0].argmax()][0]), tuple(cnts[1][cnts[1][:, :, 0].argmax()][0]))
    ext_top = min(tuple(cnts[0][cnts[0][:, :, 1].argmin()][0]), tuple(cnts[1][cnts[1][:, :, 1].argmin()][0]))
    ext_bottom = max(tuple(cnts[0][cnts[0][:, :, 1].argmax()][0]), tuple(cnts[1][cnts[1][:, :, 1].argmax()][0]))

    return (ext_left[0], ext_top[1]), (ext_right[0], ext_bottom[1])


def calibrate_screen_bounds(cam):
    img = get_image(cam)
    h, w, _ = img.shape

    cnvs = np.zeros(img.shape, np.uint8)

    cv2.rectangle(cnvs, (0, 0), (40, 50), WHITE, cv2.FILLED)
    cv2.rectangle(cnvs, (w, h), (w - 40, h - 50), WHITE, cv2.FILLED)

    corners = None
    while not corners:
        show_image_fullscreen(cnvs)

        cv2.waitKey(500)

        img = get_image(cam)
        corners = find_corners(img)

        show_image_fullscreen(img)
        cv2.waitKey(1000)

    cv2.rectangle(img, corners[0], (corners[0][0] + 10, corners[0][1] + 10), RED, cv2.FILLED)
    cv2.rectangle(img, corners[1], (corners[1][0] - 10, corners[1][1] - 10), RED, cv2.FILLED)

    # print "Corners are at: ", corners

    x1, y1, x2, y2 = corners[0][0], corners[1][0], corners[0][1], corners[1][1]

    # The edges of the screen are no good, clip them off:
    # x1, y1, x2, y2 = x1 + 20, y1, x2, y2 - 80

    return x1, y1, x2, y2
