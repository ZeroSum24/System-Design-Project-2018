#!/usr/bin/env python2

import cv2
import numpy as np
from matplotlib import pyplot as plt
import os
import sys

def main(argv):

   # accepting the image argument
   if (len(argv) != 1):
       print("Please add one image argument")
       sys.exit(2)
   imgfile = argv[0]

   img = cv2.imread(imgfile,cv2.IMREAD_GRAYSCALE)

   ret,thresh1 = cv2.threshold(img,127,255,cv2.THRESH_BINARY)
   ret,thresh2 = cv2.threshold(img,127,255,cv2.THRESH_BINARY_INV)
   ret,thresh3 = cv2.threshold(img,127,255,cv2.THRESH_TRUNC)
   ret,thresh4 = cv2.threshold(img,127,255,cv2.THRESH_TOZERO)
   ret,thresh5 = cv2.threshold(img,127,255,cv2.THRESH_TOZERO_INV)
   titles = ['Original Image','BINARY','BINARY_INV','TRUNC','TOZERO','TOZERO_INV']
   images = [img, thresh1, thresh2, thresh3, thresh4, thresh5]
   for i in xrange(6):
       plt.subplot(2,3,i+1),plt.imshow(images[i],'gray')
       plt.title(titles[i])
       plt.xticks([]),plt.yticks([])
       plt.show()

if __name__ == "__main__":
   main(sys.argv[1:])
