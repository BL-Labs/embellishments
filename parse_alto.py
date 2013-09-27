from xml.etree import ElementTree as ET

from c19_paths import *

def get_illustration_coords(doc):
  page = doc.find("Layout/Page")
  illustrations = doc.findall('Layout/Page/PrintSpace/ComposedBlock[@TYPE="Illustration"]/GraphicalElement')
  pageh, pagew = int(page.attrib['HEIGHT']), int(page.attrib['WIDTH'])
  images = []
  for img in illustrations:
    x,y = map(int, [img.attrib['HPOS'], img.attrib['VPOS']])
    h,w = map(int, [img.attrib['HEIGHT'], img.attrib['WIDTH']])
    images.append([x,y,w,h])
  return (pagew, pageh), images

def get_rect(shape):
  x,y,w,h = shape
  return [[x, y], [x+w, y+h]]

def increase_size(shape, factor, mapping, page):
  ox,oy,ow,oh = shape
  w = int(ow * mapping[0])
  x = int(ox * mapping[0])
  h = int(oh * mapping[1])
  y = int(oy * mapping[1])
  dw = (float(w) * factor) - w
  dh = (float(h) * factor) - h
  dx = dw / 2.0
  dy = dh / 2.0
  r =  [int(x - dx), int(y - dy), int(w + dw), int(h + dh)]
  # bound x
  if r[0] < 0:
    r[0] = 0
  # bound y
  if r[1] < 0:
    r[1] = 0
  # bound w
  if r[2] > page[0]:
    r[2] = page[0]
  # bound h
  if r[3] > page[1]:
    r[3] = page[1]
  return r
