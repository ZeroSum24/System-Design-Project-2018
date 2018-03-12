#!/usr/bin/env python3

# the main function would be replaced but broadly this is
# how the server module should look

import cv2
import numpy as np
import sys, getopt

from PIL import Image

import zbar
import zbar.misc
import pygame
import pygame.surfarray

def main(argv):

   # accepting the image argument
   if (len(argv) != 1):
       print("Please add one image argument")
       sys.exit(2)
   imgfile = argv[0]

   # # OpenCV: converting the image to grey_scale and appling THRESH_TOZERO
   # img = cv2.imread(imgfile,cv2.IMREAD_GRAYSCALE)
   # ret,img = cv2.threshold(img,127,255,cv2.THRESH_TOZERO)

   file_path = imgfile
   with open(file_path, 'rb') as image_file:
       image = Image.open(image_file)
       image.load()

   # scan the image for barcodes
   image_ndarray = pygame.surfarray.array3d(image)

   if len(image_ndarray.shape) == 3:
       image_ndarray = zbar.misc.rgb2gray(image_ndarray)

   scanner = zbar.Scanner()

   results = scanner.scan(img_ndarray)
   if results==[]:
       print("No Barcode found.")
   else:
       for result in results:
        # By default zbar returns barcode data as byte array, so decode byte array as ascii
            print(result.type, result.data.decode("ascii"), result.quality)

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


if __name__ == "__main__":
   main(sys.argv[1:])
