import cv2
import cv2.cv as cv

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
