# The main function would be replaced but broadly this is
# how the server module should look

#This is the pyzbar module

import os
import io
import cv2
import numpy as np
import sys, getopt
from array import array

from PIL import Image
from pyzbar.pyzbar import decode
# import zbarlight

# def scanImage(image):
def scanImage(file_path):

    # img = cv2.imread(file_path)                                                           # your image to be read ,IMREAD_COLOR =  or 1,0..
    #
    # grayscaled = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    # ret,thresh = cv2.threshold(img,127,255,cv2.THRESH_BINARY)                                 # convert to grayscale(binary image)
    # cv2.imwrite(file_path, thresh)

    # edged = cv2.Canny(thresh, 50, 50)                                                        # edge detection
    # cv2.imwrite('/Image_Test/imgs/server_images/edged.jpg', edged)
    #
    # edged, contours, hierarchy = cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)      # contour detection
    #
    # contours = sorted(contours, key=cv2.contourArea, reverse = True)[:3]                             # ! since there are three big rectangles with contours quite
    # rect_count = 0                                                                                   #   big and hence differentiable than the others.
    # for c in contours:                                                                               # we will detect abd draw the contour around that big finder pixel
    #     peri = cv2.arcLength(c, True)
    #     approx = cv2.approxPolyDP(c, 0.02*peri, True)
    #
    # if len(approx) == 4:
    #     rect_count = approx
    #
    # im1 = cv2.drawContours(img, [rect_count], -1, (0,255,0), 3)
    #
    # cv2.imwrite('/Image_Test/imgs/server_images/contours.jpg', contours)
    print("Entered image testing")
    #TODO Include Image open on the byte array to work with byte sort
    with open(file_path, 'rb') as image_file:
        image = Image.open(image_file)
        image.load()

    # scan the image for barcodes
    # returns just the data
    try:
        # codes = zbarlight.scan_codes('qrcode',image)
        codes = decode(image)
        if str(codes) == "[]":
            #Fail State is []
            return "Fail"
        else:
            #Success State is [Decoded(data=b'2', type='QRCODE')])
            print("Type: " + qr_code[24:])
            return str(codes[16])
            #pyzbar - for output: no (zbarlight ) None == [] ; yes (zbarlight [b'2'] == [Decoded(data=b'2', type='QRCODE')])

        print("Image scan success")
    except AssertionError:
        return "The File is not an image"
        # Zbarlight checks it's an image file, throwing an exception which we catch
        # and feed back to Flask

     # display_image(img)

def display_image(img):
    # displaying the altered image
    cv2.namedWindow("opencv_image", cv2.WINDOW_NORMAL)
    cv2.imshow("opencv_image", img)
    k = cv2.waitKey(0) & 0xFF
    if k == 27:         # wait for ESC key to exit
        cv2.destroyAllWindows()
    elif k == ord('s'): # wait for 's' key to save and exit
        cv2.imwrite( "../opencv_image.jpg", img)
        cv2.destroyAllWindows()
