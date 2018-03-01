# The main function would be replaced but broadly this is
# how the server module should look

import cv2
import numpy as np
import sys, getopt

from PIL import Image
import zbarlight

def scanImage(image):

   # TODO should add a check here to make sure it is an image file

   # OpenCV: converting the image to grey_scale and appling THRESH_TOZERO
   img = cv2.imread(image,cv2.IMREAD_GRAYSCALE)
   ret,img = cv2.threshold(img,127,255,cv2.THRESH_TOZERO)

   # scan the image for barcodes

   # TODO <--- this bit here needs work as it is not
   # outputting anything useful for the scanned images part
   codes = zbarlight.scan_codes('qrcode',image)
   print(codes)

   # display_image(img)

   return "Image scan success"

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
