'''
function used to analyze laser images

only contains function to retreive ellipse
'''
import cv2
import logging
import numpy as np


def getellipse(img, pixelsize = 4.65, ellipse = True):
    '''
    returns position [x, y], short axis diameter, long axis diameter in micrometers
    '''
    if img.max() == 255:
        logging.info("Camera satured, spotsize can be incorrect")
        return None
    if img.min()<0 or img.max()>255:
        logging.info("Image has wrong format")
        return None
    # Converts image from one colour space to another.
    # RGB image to gray
    imgray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    # Converts gray scale image to binary using a threshold
    ret,thresh = cv2.threshold(imgray,img.max()//2,255,cv2.THRESH_BINARY)
    # find the contours
    im2, contours, hierarchy = cv2.findContours\
                    (thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    # key function for sort *allowed sorting if multiple ellipses were detected, no longer needed.
#       def createkey(contour):
#           momA = cv2.moments(contour)        
#           (xa,ya) = int(momA['m10']/momA['m00']), int(momA['m01']/momA['m00'])
#           return xa
#               #sort contours
#           contours.sort(createkey).reverse()    
    if len(contours) == 0 or len(contours)>2:
        logging.info("Detected none or multiple spots")
        return None
    try:
        if ellipse:
            el = cv2.fitEllipse(contours[0])
        else:
            el = cv2.minEnclosingCircle(contours[0])
    except:
        logging.info("Spot not detected")
        return None
    else:
        dct = {
            'position' : list(np.array(el[0])*pixelsize),
            'axes' : np.array(el[1])*pixelsize
        }
        return dct



