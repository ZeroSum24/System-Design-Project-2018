#!/usr/bin/env python2

# the main function would be replaced but broadly this is
# how the server module should look

import cv2
import numpy as np
import sys, getopt

import Image
import zbar

def scanImage(image):

   # TODO should add a check here to make sure it is an image file

   # OpenCV: converting the image to grey_scale and appling THRESH_TOZERO
   img = cv2.imread(image,cv2.IMREAD_GRAYSCALE)
   ret,img = cv2.threshold(img,127,255,cv2.THRESH_TOZERO)

   # obtain image data
   pil = Image.fromarray(img)
   width, height = pil.size
   raw = pil.tobytes()

   # wrap image data
   image = zbar.Image(width, height, 'Y800', raw)

   # scan the image for barcodes

   # TODO <--- this bit here needs work as it is not
   # outputting anything useful for the scanned images part
   scanner = zbar.ImageScanner()
   output = scanner.scan(image)
   print output

   # extract results
   
   #TODO -- this bit may be useless (see above)
   for symbol in image:
    # do something useful with results
        print 'decoded', symbol.type, 'symbol', '"%s"' % symbol.data


   # displaying the altered image
   cv2.namedWindow("opencv_image", cv2.WINDOW_NORMAL)
   cv2.imshow("opencv_image", img)
   k = cv2.waitKey(0) & 0xFF
   if k == 27:         # wait for ESC key to exit
        cv2.destroyAllWindows()
   elif k == ord('s'): # wait for 's' key to save and exit
        cv2.imwrite('messigray.png',img)
        cv2.destroyAllWindows()

   return "Image scan success"
