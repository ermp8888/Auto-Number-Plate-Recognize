# -*- coding: utf-8 -*-
"""
Created on Tue May 11 14:02:32 2021

@author: Mohammad Parvez
"""
# import the necessary packages
import sys
sys.path.append(".")
from anpr.auto_number_plate_recognize import AutoNumberPlateRecognizer
from imutils import paths
import imutils
import cv2




def cleanup_text(text):
	# strip out non-ASCII text so we can draw the text on the image
	# using OpenCV
	return "".join([c if ord(c) < 128 else "" for c in text]).strip()


if __name__ == '__main__':
    
    objanpr = AutoNumberPlateRecognizer()
    imagePaths = sorted(list(paths.list_images("CarImages")))
    
    for imagePath in imagePaths:
        image = cv2.imread(imagePath)
        image = imutils.resize(image, width = 600)
        
        (lpText, lpCnt) = objanpr.find_and_ocr(image)
        
        if lpText is not None and lpCnt is not None:
            box = cv2.boxPoints(cv2.minAreaRect(lpCnt))
            box = box.astype("int")
            
            cv2.drawContours(image, [box], -1, (0, 255, 0), 2)
            
            (x, y, w, h) = cv2.boundingRect(lpCnt)
            
            cv2.putText(image, cleanup_text(lpText), (x, y-15), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
            
            print("[INFO] {}".format(lpText))
            cv2.imshow("Output ANPR", image)
            cv2.waitKey(0)