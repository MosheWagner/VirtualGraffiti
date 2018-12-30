import cv2

DEF_CAMERA_ID = 0


def get_cam():
    return cv2.VideoCapture(DEF_CAMERA_ID)


def get_image(cam, crop_range=None):
    _, img = cam.read()
    if not crop_range:
        return img

    # img[y:y+h, x:x+w, :]
    cropped = img[crop_range[2]:crop_range[3], crop_range[0]:crop_range[1], :]

    return cropped
