import cv2
import cv2.cv as cv

import numpy as np
import math as m

CASCADES = {
    'face': cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_alt.xml'),
#    'frontalt': cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_alt.xml'),
    'profile': cv2.CascadeClassifier('haarcascades/haarcascade_profileface.xml'),
    'upperbody': cv2.CascadeClassifier('haarcascades/haarcascade_upperbody.xml'),
#    'eye': cv2.CascadeClassifier('haarcascades/haarcascade_eye.xml'),
    'fullbody': cv2.CascadeClassifier('haarcascades/haarcascade_fullbody.xml'),
           }

CASCADE_COLOUR = {
    'n_front': (0, 255, 0),
    'r_front': (255, 0, 0),
    'profile': (255, 0, 0),
    'frontalt': (255, 255, 0),
    'upperbody': (0, 0, 255),
}

def rotate90(img):
  # timg = cv.CreateImage((img.height,img.width), img.depth, img.channels) # transposed image

  # rotate clockwise
  timg = cv2.transpose(img)
  timg = cv2.flip(timg, 1)
  return timg

def detect(inputimg, scaleFactor=1.2, minNeighbors=4, minSize=(20, 20),
           flags=cv.CV_HAAR_SCALE_IMAGE):
  rectlist = {}
  hit = False
  for t, img in [("n_", inputimg), ("r_", rotate90(inputimg))]:
    for cascade_type, cascade in CASCADES.iteritems():
      rects = cascade.detectMultiScale(img, scaleFactor=scaleFactor,
                                     minNeighbors=minNeighbors,
                                     minSize=minSize, flags=flags)
      if len(rects) == 0:
        rectlist[t+cascade_type] = []
      else:
        rects[:, 2:] += rects[:, :2]
        hit = True
        rectlist[t+cascade_type] = rects
  return rectlist, hit

def explain_houghp_lines(filename, a=150, b=200, c=60, d=20, e=10):
  img = cv2.imread(filename)
  grey = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
  cv2.imwrite(filename+"grey.jpg", grey)
  edges = cv2.Canny(grey,a,b,apertureSize = 3)
  cv2.imwrite(filename+"edges.jpg", edges)
  lines = cv2.HoughLinesP(edges, e,np.pi/180, 300, minLineLength = c, maxLineGap = d)
  if lines != []:
    for x1,y1,x2,y2 in lines[0]:
      cv2.line(img,(x1,y1),(x2,y2),(0,255,0),2)
    cv2.imwrite(filename+'houghlines.jpg',img)

def houghp_lines(filename, a=150, b=200, c=60, d=20, e=20):
  img = cv2.imread(filename)
  grey = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
  edges = cv2.Canny(grey,a,b,apertureSize = 3)
  lines = cv2.HoughLinesP(edges,e,np.pi/180, 300, minLineLength = c, maxLineGap = d)
  if lines != None:
    return lines
  else:
    return [[]]

def houghp_circles(filename, a=2, b=80, c=100, d=100, e=50, f=150):
  img = cv2.imread(filename)
  grey = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
  circles = cv2.HoughCircles(grey, cv2.cv.CV_HOUGH_GRADIENT, a, b, None, c, d, e, f)
  if circles != None:
    return circles, img.shape
  else:
    return [], img.shape

def polar_lines(lines):
  polar = []
  for x1,y1,x2,y2 in lines[0]:
    x = x2 - x1
    y = y2 - y1
    XsqPlusYsq = x**2 + y**2
    r = m.sqrt(XsqPlusYsq)
    theta = m.atan2(y, x)
    polar.append((r,theta))
  return polar

def slantyness(filename, a=150, b=200, c=60, d=20, e=20):
  # faking a subjective measure
  # takes the probabalistic hough lines, and combines them (intentionally without mathematical rigour!)
  # to form an average 'gradient' for the image
  lines = houghp_lines(filename, a=a, b=b, c=c, d=d, e=20)
  polarlines = polar_lines(lines)
  slants = [(1 - m.cos(4*line[1])) for line in polarlines]
  
  # ave. closer to 0, predominately horiz+vert lines
  # closer to 1,      "        slanted lines
  if slants:
    return sum(slants)/ float(len(slants))
  else:
    return

def aspectratio(filename, a=150, b=200, c=60, d=20, e=20):
  lines = houghp_lines(filename, a=a, b=b, c=c, d=d, e=20)
  polarlines = polar_lines(lines)
  horiz = [(r,th) for r, th in polarlines if np.abs(th) < np.pi/8]
  verts = [(r,th) for r, th in polarlines if np.abs(th) > 3*np.pi/8]
  hbias = sum(map(lambda x: x[0], horiz))
  vbias = sum(map(lambda x: x[0], verts))
  return hbias, vbias

def bubblyness(filename, a=2, b=80, c=100, d=100, e=20, f=150):
  circles, shape = houghp_circles(filename, a,b,c,d,e,f)
  h,w,_ = shape
  midx = int(w/2)
  midy = int(h/2)
  if circles != []:
    sizes = [x[2] for x in circles[0]]
    xs = [midx - x[0] for x in circles[0]]
    ys = [midy - x[1] for x in circles[0]]
    return sum(sizes), sum(sizes)/float(len(sizes)), sum(xs)/float(len(xs)), sum(ys)/float(len(ys)) 
  else:
    return 0,0,0,0
