'''
function used to analyze laser images

only contains function to retreive ellipse
'''
import cv2
import logging


def getellipse(img):
    '''
    prints short and long axis and returns ellipse detected in supplied image

    '''
    pixelsize = 4.65 # micrometers
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
    # Values below 127 are mapped to 0 and values above 127 are mapped to 255
    ret,thresh = cv2.threshold(imgray,127,255,cv2.THRESH_BINARY)
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
        el = cv2.fitEllipse(contours[0])
        logging.info('Short axis: '+str(round(el[1][0]*pixelsize,2))+' micrometers.')
        logging.info('Long axis: '+str(round(el[1][1]*pixelsize,2))+' micrometers.')
        return el
    except:
        logging.info("Spot not detected")
        return None




