import os
import cv2
import numpy as np
import imutils
import ctypes

def showGreen(image):
    # create NumPy arrays from the boundaries
    lower = np.array([0,0,180], dtype = "uint8")
    upper = np.array([100,100,255], dtype = "uint8")
 
    # find the colors within the specified boundaries and apply
    # the mask
    mask = cv2.inRange(image, lower, upper)
    output = cv2.bitwise_and(image, image, mask = mask)
 
    # show the images
    #cv2.imshow("images", np.hstack([image, output]))
    #cv2.waitKey(0)
    return output


last_image = None
def mark_delta_rects(color_img, canvas, color, radius):
    global last_image
    gray = cv2.cvtColor(color_img, cv2.COLOR_BGR2GRAY)
    
    diff = None
    if last_image is not None:
        frameDelta = cv2.absdiff(last_image, gray)
        thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        x,y,w,h = find_small_rect(cnts)
        #rs = rects(cnts)
        #for x,y,w,h in rs:
            # x,y,w,h = find_small_rect(cnts)
        centerx, centery = x + (w/2), y + (h/2)
        cv2.circle(canvas, (centerx, centery), radius, color, thickness=cv2.FILLED)
            
        return canvas
    
    
    last_image = gray
    return color_img


def find_small_rect(cnts):
    cnts = cnts[0] if imutils.is_cv2() else cnts[1]
    max_area = 0
    max_c = None
    # loop over the contours
    for c in cnts:
        area = cv2.contourArea(c)
        # if the contour is too small, ignore it
        #if area > 100:  # Tune this!
        #    continue
            
        #if area < 20:  # Tune this!
        #    continue
 
        if area > max_area:
            max_area = area
            max_c = c
 
    # compute the bounding box for the contour, draw it on the frame,
    # and update the text
    (x, y, w, h) = cv2.boundingRect(max_c)
    return x, y, w, h
    
    
    
def approx_change(color_img, canvas, color, radius):
    global last_image
    gray = cv2.cvtColor(color_img, cv2.COLOR_BGR2GRAY)
    
    diff = None
    if last_image is not None:
        frameDelta = cv2.absdiff(last_image, gray)
        thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
        _, cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            extLeft = tuple(c[c[:, :, 0].argmin()][0])
            extRight = tuple(c[c[:, :, 0].argmax()][0])
            extTop = tuple(c[c[:, :, 1].argmin()][0])
            extBot = tuple(c[c[:, :, 1].argmax()][0])
            
            cv2.line(canvas, extLeft, extRight, color, thickness=radius)
            
        return canvas
    
    
    last_image = gray
    return color_img

canvas = None

def get_image(cam, crop_range = None):
    _, img = cam.read()
    if not crop_range:
        return img
    # img[y:y+h, x:x+w]
    return img[crop_range[2]:crop_range[3], crop_range[0]:crop_range[1], :]

    
    
# TODO: Call this only once
def get_screen_size():
    if os.name != 'nt':
        raise Exception('Auto screen size only supported on windows for now!')
        
    user32 = ctypes.windll.user32
    # TODO: If you are using 2 screens, make sure this returns the correct value
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def show_image_fullscreen(img):
    h = img.shape[0]
    w = img.shape[1]
    sw, sh = get_screen_size()
    wf, hf = sw/float(w), sh/float(h) 

    # Resize image to screen size
    
    fs_img = cv2.resize(img, (0,0), fx=wf, fy=hf)

    cv2.namedWindow("IMG", cv2.WND_PROP_FULLSCREEN)  # Create a named window
    cv2.moveWindow("IMG", 0,0)  # When displayin on a different monitor, muse this offset to push it to there
    cv2.setWindowProperty("IMG", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.imshow("IMG", fs_img)

"""
class ScreenDisp:
    def __init__(self):
        sw, sh = get_screen_size()
"""        
 
BLACK = (0, 0, 0) 
BLUE = (255, 0, 0)
GREEN = (0, 255, 0)
RED = (0, 0, 255)
YELLOW = (0, 255, 255)
WHITE = (255, 255, 255)

def show_webcam(cam, mirror=False):
    global canvas
    color = GREEN
    radius = 5

    while True:
        img = get_image(cam)
        # ret_val, img = cam.read()
        if canvas is None:
            canvas = np.zeros(img.shape, np.uint8)
        
        img = showGreen(img)
        #canvas = mark_delta_rects(img, canvas, color, radius)
        canvas = approx_change(img, canvas, color, radius)

        disp_img = canvas
        if mirror:
            #img = cv2.flip(img, 1)
            disp_img = cv2.flip(disp_img.copy(), 1)
        show_image_fullscreen(disp_img)
        
        k = cv2.waitKey(3)
        
        if k == ord('w'): 
            color = WHITE
        elif k == ord('g'): 
            color = GREEN
        elif k == ord('b'): 
            color = BLUE  
        elif k == ord('y'): 
            color = YELLOW
        elif k == ord('c'): 
            canvas = np.zeros(img.shape, np.uint8)
            radius = 5  # Back to normal size
            global last_image
            last_image = None
        elif k == ord('['): 
            radius += 1
        elif k == ord(']'): 
            if radius > 1:
                radius -= 1
        
    cv2.destroyAllWindows()

LASER_RED = (20, 20, 250)
def do_graffiti(cam, bounds, mirror=False):
    
    img = get_image(cam, bounds)
    canvas = np.zeros(img.shape, np.uint8)
    
    while True:
        img = get_image(cam, bounds)
        
        filtered = filter_color(img, LASER_RED)
        
        blurred = cv2.GaussianBlur(filtered, (5, 5), 0)
        thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)[1]
        _, cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for c in cnts: 
            x, y, w, h = cv2.boundingRect(c)
            # draw a rectangle to visualize the bounding rect
            cv2.rectangle(canvas, (x, y), (x+w, y+h), GREEN, 2)

        # show_image_fullscreen(canvas)
        show_image_fullscreen(img)
        k = cv2.waitKey(3)
        
        if k == ord('c'): 
            canvas = np.zeros(img.shape, np.uint8)
            radius = 5  # Back to normal size

    
    
def byte_clip(v):
    if v < 0:
        return 0
    if v > 255:
        return 255
    return v
    
COLOR_THRESH = 75
def filter_color(img, color):
    # create NumPy arrays from the boundaries
    lower = np.array([byte_clip(c - COLOR_THRESH) for c in color], dtype = "uint8")
    upper = np.array([byte_clip(c + COLOR_THRESH) for c in color], dtype = "uint8")
 
    # find the colors within the specified boundaries and apply the mask
    mask = cv2.inRange(img, lower, upper)
    output = cv2.bitwise_and(img, img, mask = mask)
    gray = cv2.cvtColor(output, cv2.COLOR_BGR2GRAY)

    return gray
   
   
def is_close(n1, n2, thresh=0.05, min_diff=1):
    if abs(n1-n2) < min_diff:
        return True
    return abs(n1-n2)/float(n1) < thresh and abs(n1-n2)/float(n2) < thresh
   
   
MIN_CORNER_SIZE = 100
def is_square(c):
    # A few quick heuristics to check if it's actually a square:
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.04 * peri, True)
    
    if len(approx) != 4:
        return False
        
    (x, y, w, h) = cv2.boundingRect(approx)
    ar = w / float(h)     
    
    if not is_close(ar, 1):
        return False
    
    if cv2.contourArea(approx) < MIN_CORNER_SIZE:
        return False
    
    return True
    
    #if is_close(cv2.contourArea(c), extLeft.x-extRight.x

def find_corners(img):
    # Filter our all but green
    filtered =  filter_color(img, WHITE)

    blurred = cv2.GaussianBlur(filtered, (5, 5), 0)
    thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)[1]
    _, cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for c in cnts: 
        x, y, w, h = cv2.boundingRect(c)
        # draw a rectangle to visualize the bounding rect
        cv2.rectangle(img, (x, y), (x+w, y+h), RED, 2)

    show_image_fullscreen(img)
    cv2.waitKey(500)
    
    cnts = [c for c in cnts if is_square(c)]
    
    assert len(cnts) == 2
    
    
    extLeft = min(tuple(cnts[0][cnts[0][:, :, 0].argmin()][0]), tuple(cnts[1][cnts[1][:, :, 0].argmin()][0]))
    extRight = max(tuple(cnts[0][cnts[0][:, :, 0].argmax()][0]), tuple(cnts[1][cnts[1][:, :, 0].argmax()][0]))
    extTop = min(tuple(cnts[0][cnts[0][:, :, 1].argmin()][0]), tuple(cnts[1][cnts[1][:, :, 1].argmin()][0]))
    extBot = max(tuple(cnts[0][cnts[0][:, :, 1].argmax()][0]), tuple(cnts[1][cnts[1][:, :, 1].argmax()][0]))
    
    return (extLeft[0], extTop[1]), (extRight[0], extBot[1])
    

def calibrate(cam):
    img = get_image(cam)
    h,w,_ = img.shape
    
    cnvs = np.zeros(img.shape, np.uint8)
    
    cv2.rectangle(cnvs, (0,0), (50,50), WHITE, cv2.FILLED)
    cv2.rectangle(cnvs, (w,h), (w-50,h-50), WHITE, cv2.FILLED)
    
    show_image_fullscreen(cnvs)
    
    cv2.waitKey(500)
    
    img = get_image(cam)
    corners = find_corners(img)
    
    cv2.rectangle(img, corners[0], (corners[0][0]+10,corners[0][1]+10), RED, cv2.FILLED)
    cv2.rectangle(img, corners[1], (corners[1][0]-10,corners[1][1]-10), RED, cv2.FILLED)
    show_image_fullscreen(img)
    
    cv2.waitKey(500)
    
    print corners
    
    x1, y1, x2, y2 = corners[0][0],corners[1][0],corners[0][1],corners[1][1]
    
    return x1,y1,x2,y2
    # img = get_image(cam, [x1, y1, x2, y2])
    # 
    # cnvs = np.zeros(img.shape, np.uint8)
    # h,w,_ = img.shape
    # cv2.rectangle(cnvs, (0, 0), (50,50), GREEN, cv2.FILLED)
    # cv2.rectangle(cnvs, (w,h), (w-50,h-50), RED, cv2.FILLED)
    # 
    # show_image_fullscreen(cnvs)
    # 
    # cv2.waitKey(5000)
    


def main():
    cam = cv2.VideoCapture(0)
    bounds = calibrate(cam)   

    do_graffiti(cam, bounds, mirror=False)
    
    # show_webcam(cam, mirror=False)


if __name__ == '__main__':
    main()