import streamlit as st 
from PIL import Image
import numpy as np
import cv2
import pytesseract
import bs4 as bs
import urllib.request
import re
import nltk
import pyttsx3
from urllib.request import Request, urlopen
import heapq

def getSkewAngle(cvImage) -> float:
    newImage = cvImage.copy()
    gray = cv2.cvtColor(newImage, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (9, 9), 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
    dilate = cv2.dilate(thresh, kernel, iterations=5)

    contours, hierarchy = cv2.findContours(dilate, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key = cv2.contourArea, reverse = True)

    largestContour = contours[0]
    minAreaRect = cv2.minAreaRect(largestContour)

    angle = minAreaRect[-1]
    if angle < -45:
        angle = 90 + angle
    return -1.0 * angle
def rotateImage(cvImage, angle: float):
    newImage = cvImage.copy()
    (h, w) = newImage.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    newImage = cv2.warpAffine(newImage, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return newImage


def deskew(cvImage):
    angle = getSkewAngle(cvImage)
    return rotateImage(cvImage, -1.0 * angle)

def remove_shadow(img_rgb):
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    rgb_planes = cv2.split(img_rgb)

    result_planes = []
    result_norm_planes = []
    for plane in rgb_planes:
        dilated_img = cv2.dilate(plane, np.ones((7,7), np.uint8))
        bg_img = cv2.medianBlur(dilated_img, 21)
        diff_img = 255 - cv2.absdiff(plane, bg_img)
        norm_img = cv2.normalize(diff_img,None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
        result_planes.append(diff_img)
        result_norm_planes.append(norm_img)

    result = cv2.merge(result_planes)
    result_norm = cv2.merge(result_norm_planes)
    return result_norm

def threshold(result_norm):
    gray = cv2.cvtColor(result_norm, cv2.COLOR_RGB2GRAY)
    thres=cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return thres

def rotate(thres):
    val=pytesseract.image_to_osd(thres)
    if(val[50:53]=='270' ):
        thres = cv2.rotate(thres, cv2.ROTATE_90_COUNTERCLOCKWISE) 
    elif(val[51:53]=='90'):
        thres = cv2.rotate(thres, cv2.ROTATE_90_CLOCKWISE) 
    elif(val[50:53]=='180'):
        thres = cv2.rotate(thres, cv2.ROTATE_180) 
    return thres
def preprocess_image(img):
    global img_cv
    img_cv=img.copy()
    img_cv = deskew(img_cv)
    result_norm = remove_shadow(img_cv)
    thres = threshold(result_norm)
    thres = rotate(thres)
    return thres
def get_img():
    uploaded_file = st.file_uploader("Choose an image...", type=["png",'jpg','jpeg'])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Image.', use_column_width=True)
        pil_image = Image.open(uploaded_file).convert('RGB') 
        open_cv_image = np.array(pil_image) 
        open_cv_image = open_cv_image[:, :, ::-1].copy() 
        thres= preprocess_image(open_cv_image)
        text= pytesseract.image_to_string(thres)
        paragraphs=text
        article_text = ""
        article_text =paragraphs
        # Removing Square Brackets and Extra Spaces
        article_text = re.sub(r'\[[0-9]*\]', ' ', article_text)
        article_text = re.sub(r'\s+', ' ', article_text)
        # Removing special characters and digits
        formatted_article_text = re.sub('[^a-zA-Z]', ' ', article_text )
        formatted_article_text = re.sub(r'\s+', ' ', formatted_article_text)
        return formatted_article_text