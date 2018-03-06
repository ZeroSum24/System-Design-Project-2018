# The main function would be replaced but broadly this is
# how the server module should look

import os
import io
import cv2
import numpy as np
import sys, getopt
from array import array

from PIL import Image
import zbarlight

# def scanImage(image):
def scanImage(file_path):

    #TODO Include Image open on the byte array to work with byte sort
    with open(file_path, 'rb') as image_file:
        image = Image.open(image_file)
        image.load()
    # scan the image for barcodes
    try:
        codes = zbarlight.scan_codes('qrcode',image)
        return str(codes)
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
