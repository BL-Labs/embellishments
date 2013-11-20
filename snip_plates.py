import time
import os, sys
from redis import Redis
import numpy as np

import re

from zipfile import ZipFile

from c19_paths import *

from parse_alto import *
from parse_xml import parse_xml

tmp_path = "/tmp/tmpimgs"

embellish_path = "/mnt/nas/plates"
plateimgs = "platesimages"

if not os.path.isdir(embellish_path):
  os.mkdir(embellish_path)

r = Redis()

wq = "platesq"

def make_safe(title):
  return re.sub(r'[^A-z0-9\s]', ' ', title)

def extract_jp2(zp, filename):
  print("Extracting {0}".format(filename))
  zp.extract(filename, tmp_path)
  return os.path.join(tmp_path, filename)

def delete_jp2(filename):
  try:
    os.remove(os.path.join(tmp_path, filename))
  except OSError, e:
    print("Couldn't delete {0} from {1}".format(filename, tmp_path))

def get_job(workerid):
  if r.llen(workerid) == 0:
    status = ""
    while(status == ""):
      status = r.rpoplpush(wq, workerid)
      if status == "":
        r.lrem(workerid, job, 1)
    return status
  else:
    return r.lrange(workerid, 0, 0)[0]

def clear_job(workerid, job):
  r.lrem(workerid, job, 1)

def get_extent(ident, filename):
  # eg /path/to/thing/000000478_0_1-212pgs__999448_dat.zip
  fn = filename.split("/")[-1]
  id, vol, pages, _ = fn.split("_", 3)
  if id == ident:
    # sanity check
    start, end = map(int, pages[:-3].split("-"))
    return start, end
  else:
    print("Supplied id '{0}' didn't match zipfile id '{1}'".format(ident, id))
    return 0, 100000 

def snip_illustrations(zp, filename, altoxmloldpath, scale = 1.1, threshold = 1200*600, zipfilename=""):
    id, vol, page = altopath_to_idvol(altoxmloldpath)
    start, end = get_extent(id, zipfilename)
    if int(page) == start or int(page) == end:
      print("This looks like the book cover - page '{0}' - extent ({1}, {2})".format(int(page), start, end))
      return
    
    altofilepath = old_winpath_to_vmpath(altoxmloldpath)
    doc = []
    with open(altofilepath, "r") as xmlfile:
      doc = ET.fromstring(xmlfile.read())
    page_shape, images = get_illustration_coords(doc)
    if images and [x for x in images if x[2]*x[3] > threshold]:
      counter = 0
      img_color = cv2.imread(extract_jp2(zp, filename))
      delete_jp2(filename)
      h,w,_ = img_color.shape
      current_page_shape = (w,h)
      dh = float(h)/float(page_shape[1])
      dw = float(w)/float(page_shape[0])
      identifier, title, author, pubplace, publisher, guesseddate = parse_xml(id)
      for rect in images:
        counter += 1
        if rect[2]*rect[3] > threshold:
          print("Attempting to slice '{1}' from {0}".format(filename, rect))
          scaled = increase_size(rect, scale, (dw,dh), current_page_shape)
          boundary = get_rect(scaled)
          if len(guesseddate) != 4:
            guesseddate = "Unknown"
          if not os.path.exists(os.path.join(embellish_path, guesseddate)):
            os.mkdir(os.path.join(embellish_path, guesseddate))
          img_filename = os.path.join(embellish_path, guesseddate, "{0}_{1}_{2}_{3}_{4}_{5}.jpg".format(id, vol, page, counter, make_safe(title), guesseddate))
          short_filename = os.path.join(embellish_path, guesseddate, "{0}_{1}_{2}_{3}_{4}_{5}.jpg".format(id, vol, page, counter, make_safe(title)[:80], guesseddate))
          # if not already captured this, switch to new short title and carry on
          if not os.path.exists(img_filename):
            img_filename = short_filename
          # Has this been captured before?
          try:
            if not os.path.exists(img_filename):
              cv2.imwrite(img_filename, img_color[boundary[0][1]:boundary[1][1], boundary[0][0]:boundary[1][0]], [cv2.cv.CV_IMWRITE_JPEG_QUALITY, 93] )
              if os.path.isfile(img_filename):
                r.lpush(plateimgs, img_filename)
                noplates = r.llen(plateimgs)
                print("Plate no: {1} - {0}".format(img_filename, noplates))
              else:
                print("CV2 SECRETLY FAILED...")
                r.lpush("plateerror", altoxmloldpath)
            else:
              print("Already captured, skipping")
          except:
            img_filename = os.path.join(embellish_path, guesseddate, "{0}_{1}_{2}_{3}_{4}.jpg".format(id, vol, page, counter, guesseddate))
            cv2.imwrite(img_filename, img_color[boundary[0][1]:boundary[1][1], boundary[0][0]:boundary[1][0]], [cv2.cv.CV_IMWRITE_JPEG_QUALITY, 93])
            if os.path.isfile(img_filename):
              r.lpush(plateimgs, img_filename)
              noplates = r.llen(plateimgs)
              print("Plate no: {1} - {0}".format(img_filename, noplates))
            else:
              print("CV2 SECRETLY FAILED...")
              r.lpush("plateerror", altoxmloldpath)
    else:
      print("All illustration areas in {1}(vol:{2}, pg: {3} are below threshold area size (currently: {0})".format(threshold, id, vol, page))

if __name__ == "__main__":
  workerid = "plateswrk"+sys.argv[1]
  while(True):
    jobs = get_job(workerid)
    while(jobs):
      joblist = jobs.split("\t")
      print("Trying to open {0}".format(joblist[0]))
      zipfilename = altopath_to_jp2_zip(joblist[0])
      print(zipfilename)
      try:
        with ZipFile(zipfilename, "r") as zipf:
          for job in joblist:
            img_filename = altopath_to_imagename(job)
            snip_illustrations(zipf, img_filename, job, scale = 1.25, threshold = 1000*1000, zipfilename=zipfilename)
        clear_job(workerid, jobs)
      except AttributeError, e:
        print e
        print("Problematic zip file - likely a series of volumes not indicated in metadata/filenames")
        print("from '{0}...'".format(joblist[0]))
        r.rpoplpush(workerid, "plateproblems")
      jobs = get_job(workerid)
    if jobs == "":
      clear_job(workerid, jobs)
      jobs = get_job(workerid)
    else:
      print("%s ran out of jobs - waiting for 5 seconds before checking again" % workerid)
      time.sleep(5)
