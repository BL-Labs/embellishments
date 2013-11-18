from xml.etree import ElementTree as ET

from c19_paths import *

def get_illustration_coords(doc, component="PrintSpace"):
  page = doc.find("Layout/Page")
  illustrations = doc.findall('Layout/Page/{0}/ComposedBlock[@TYPE="Illustration"]/GraphicalElement'.format(component))
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

def get_attrib_rect(enode):
  x,y = map(int, [enode.attrib['HPOS'], enode.attrib['VPOS']])
  h,w = map(int, [enode.attrib['HEIGHT'], enode.attrib['WIDTH']])
  return (x,y,w,h)

def characterise(doc):
  page = doc.find("Layout/Page")
  
  # <Page ID="P27" PHYSICAL_IMG_NR="27" HEIGHT="2579" WIDTH="1569" POSITION="Right" ACCURACY="53.41">
  #			<TopMargin ID="P27_TM00001" HPOS="0" VPOS="0" WIDTH="1568" HEIGHT="320"/>
  #			<LeftMargin ID="P27_LM00001" HPOS="0" VPOS="320" WIDTH="38" HEIGHT="2009"/>

  page_position = page.attrib['POSITION']
  page_shape, images = get_illustration_coords(doc)

  leftmargin = page.find("LeftMargin")
  rightmargin = page.find("RightMargin")
  page_left_margin = get_attrib_rect(leftmargin)
  page_right_margin = get_attrib_rect(rightmargin)
  
  printblock = page.find("PrintSpace")
  printblock_shape = get_attrib_rect(printblock)

  return {'page': page_shape,
          'orientation': page_position,
          'leftmargin': page_left_margin,
          'rightmargin': page_right_margin,
          'printspace': printblock_space,
          'images':images}
  
