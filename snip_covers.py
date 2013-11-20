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

cover_path = "/mnt/nas/covers"

if not os.path.isdir(cover_path):
  os.mkdir(cover_path)

r = Redis()

wq = "coverq"
output = "coveroutput"

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

def snip_illustrations(zp, filename, id, vol, page):
  try:
    img_color = cv2.imread(extract_jp2(zp, filename))
    delete_jp2(filename)
    identifier, title, author, pubplace, publisher, guesseddate = parse_xml(id)
    if not os.path.exists(os.path.join(cover_path, guesseddate)):
      os.mkdir(os.path.join(cover_path, guesseddate))
    cv2.imwrite(os.path.join(cover_path, guesseddate, "{0}_{1}_{2}_{3}.jpg".format(id, vol, make_safe(title), guesseddate)), img_color, [cv2.cv.CV_IMWRITE_JPEG_QUALITY, 93] )
    print("{0}_{1}_{2}_{3}.jpg".format(id, vol, make_safe(title), guesseddate))
  except KeyError, e:
    r.rpoplpush(workerid, "coverproblems")

if __name__ == "__main__":
  workerid = "coverwrk"+sys.argv[1]
  while(True):
    job = get_job(workerid)
    while(job):
      zipfilename = os.path.join("/mnt/nas/JP2", job)
      print(zipfilename)
      try:
        with ZipFile(zipfilename, "r") as zipf:
          id, vol, _ = job.split("_", 2)
          img_filename = "JP2\\%s_%02d_%s.jp2" % (id, int(vol), "000001")
          if vol == "0" or vol == "00":
            img_filename = "JP2\\{0}_{1}.jp2".format(id, "000001")
          snip_illustrations(zipf, img_filename, id, vol, "000001")
        clear_job(workerid, job)
      except AttributeError, e:
        print e
        print("Problematic zip file - likely a series of volumes not indicated in metadata/filenames")
        print("from '{0}...'".format(joblist[0]))
        r.rpoplpush(workerid, "coverproblems")
      job = get_job(workerid)
    print("%s ran out of jobs - waiting for 5 seconds before checking again" % workerid)
    time.sleep(5)
