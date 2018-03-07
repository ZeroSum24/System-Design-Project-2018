# The main function would be replaced but broadly this is
# how the server module should look

#This is the Data Matrix module

import os
import io
import cv2
import numpy as np
import sys, getopt
from array import array

from PIL import Image
from pylibdmtx.pylibdmtx import decode

def scanImage(file_path):

    print("Entered image testing")

    with open(file_path, 'rb') as image_file:
        image = Image.open(image_file)
        image.load()

    # scan the image for barcodes
    # return a "Fail" string or a int if successful
    try:
        codes = decode(image)
        if str(codes) == "[]":
            #Fail State is []
            return "Fail"
        else:
            #Success State is [Decoded(data=b'2', type='QRCODE')])
            print("Type: " + str(codes[24:]))
            print(str(codes))
            print(str(codes)[16])
            return str(codes)[16]

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
