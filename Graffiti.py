"""
Simply display the contents of the webcam with optional mirroring using OpenCV 
via the new Pythonic cv2 interface.  Press <esc> to quit.
"""

import cv2
import numpy as np
import imutils


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

def get_image(cam):
    _, img = cam.read()
    return img[100:700, 200:1400]


def show_image(img):
    cv2.namedWindow("IMG")        # Create a named window
    cv2.moveWindow("IMG", 0,0)
    cv2.imshow("IMG", img)

GREEN = (0, 255, 0)
BLUE = (255, 0, 0)
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
        disp_img = cv2.resize(disp_img, (0,0), fx=2.5, fy=2)
        if mirror:
            #img = cv2.flip(img, 1)
            disp_img = cv2.flip(disp_img.copy(), 1)
        show_image(disp_img)
        
        k = cv2.waitKey(2)
        
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



def calibration_phase(cam):
    while True:
        img = get_image(cam)
        #ret_val, img = cam.read()
        show_image(cv2.resize(img, (0,0), fx=2.5, fy=2))
        
        if cv2.waitKey(2) == 27: 
            break  # esc to quit
    cv2.destroyAllWindows()




def main():
    cam = cv2.VideoCapture(0)
    calibration_phase(cam)   

    show_webcam(cam, mirror=False)


if __name__ == '__main__':
    main()