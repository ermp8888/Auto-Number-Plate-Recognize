# -*- coding: utf-8 -*-
"""
Created on Tue May 11 12:44:34 2021

@author: Mohammad Parvez
"""

# import the necessary packages
from skimage.segmentation import clear_border
import pytesseract
import numpy as np
import imutils
import cv2


pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'


class AutoNumberPlateRecognizer:
    
    def __init__(self, minAr = 4, maxAr = 5, debug = True):
        
        # minAr and maxAr stores the aspect ratio value of rectangle, by default it is 4 and 5
        self.minAr = minAr 
        self.maxAr = maxAr
        self.debug = debug # It control the debugging of the program
        
        
    def debug_imshow(self, title, image, waitKey = False):
        
        # If we are in debug mode, then show intermediate results
        if self.debug:
            cv2.imshow(title, image)
            
            if waitKey:
                cv2.waitKey(0)
        
        
    def locate_license_plates_return_threshold(self, gray):
        
        # perform a blackhat morphological operation on the grayscale image
        # Define rectangular kernel using cv2.getStructuringElement method
        rectKern = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 5))
        blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, rectKern)
        self.debug_imshow("blackhat", blackhat)
        
        
        # Using Morphology and thresholding find the light regions in the processed image 
        squareKern = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        light = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, squareKern)
        light = cv2.threshold(light, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        self.debug_imshow("Light Region", light)
        
        
        
        # compute the Scharr gradient representation of the blackhat
		# image in the x-direction and then scale the result back to
		# the range [0, 255]
        gradX = cv2.Sobel(blackhat, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
        gradX = np.absolute(gradX)
        (minVal, maxVal) = (np.min(gradX), np.max(gradX))
        gradX = 255 * ((gradX - minVal) / (maxVal - minVal))
        gradX = gradX.astype("uint8")
        self.debug_imshow("Scharr", gradX)
        
        # Apply GaussianBlur to blur the gradient representation, apply closing operation
        # and using otsu's method threshold it.
        gradX = cv2.GaussianBlur(gradX, (5, 5), 0)
        gradX = cv2.morphologyEx(gradX, cv2.MORPH_CLOSE, rectKern)
        thresh = cv2.threshold(gradX, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        self.debug_imshow("Grad Thresh", thresh)
        
        
        # For cleaning the thresholded image apply erosion and dialation filters.
        thresh = cv2.erode(thresh, None, iterations=2)
        thresh = cv2.dilate(thresh, None, iterations=2)
        self.debug_imshow("Grad Erode/Dilate", thresh)
        
        
        # apply bitwise AND operation between the threshold result and the
		# light regions of the image
        thresh = cv2.bitwise_and(thresh, thresh, mask=light)
        thresh = cv2.dilate(thresh, None, iterations=2)
        thresh = cv2.erode(thresh, None, iterations=1)
        self.debug_imshow("Final", thresh, waitKey = True)
        
        # return the thresholded output image
        return thresh
    
    
    
                
    def find_contours(self, thresh, keep = 5):
        
        # find contours in the thresholded image and sort them by
		# their size in descending order, keeping only the largest
		# ones
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:keep]
        
        return cnts
    
    
    def locate_license_plate(self, gray, contours):
        lpCnt = None
        roi = None
        
        for c in contours:
            (x, y, w, h) = cv2.boundingRect(c)
            ar = w / float(h)
            #print(ar)
            
            if ar >= self.minAr and ar <= self.maxAr:
                lpCnt = c
                licensePlate = gray[y:y+h, x:x+w]
                roi = cv2.threshold(licensePlate, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        
                self.debug_imshow("License Plate", licensePlate)
                self.debug_imshow("ROI", roi)
        return (roi, lpCnt)
    
    
    def build_tesseract_option(self, psm = 7):
        alphanumeric = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        options = "-c tessedit_char_whitelist={}".format(alphanumeric)
        options += " --psm {}".format(psm)
        
        return options
    

    def find_and_ocr(self, image):
        #image = cv2.imread("C://Users//Mohammad Parvez//Desktop//Chegg//opencv-anpr//license_plates//group1//008.jpg")
        #image = imutils.resize(image, width=600)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        self.debug_imshow("Original Image", gray)
        
        thresh = self.locate_license_plates_return_threshold(gray)
        contours = self.find_contours(thresh)
        (lp, lpCnt) = self.locate_license_plate(gray, contours)
        
        lpText = None
        
        if lp is not None:
            option = self.build_tesseract_option(psm = 7)
            lpText = pytesseract.image_to_string(lp, config=option)
            self.debug_imshow("License plate", lp)
            
        return (lpText, lpCnt)
    