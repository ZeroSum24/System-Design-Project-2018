#!/usr/bin/env python3

import cv2
import numpy as np
from matplotlib import pyplot as plt
import os

import sys, getopt

def main(argv):
   if (len(argv) != 1):
       print("Please add one image argument")
       sys.exit(2)
   imgfile = argv[0]
   img = cv2.imread(imgfile,cv2.IMREAD_GRAYSCALE)

   ret,img = cv2.threshold(img,127,255,cv2.THRESH_TOZERO)
   cv2.imwrite( "../opencv_image.jpg", img)

if __name__ == "__main__":
   main(sys.argv[1:])
