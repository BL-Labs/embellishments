import os
from redis import Redis

import time

r = Redis()

uri = "{0}/{1}"
root = "/mnt/nas/embellishments"
p = r.pipeline()
count = 1
for year in sorted([x for x in os.listdir(root) if os.path.isdir(os.path.join(root, x))]):
  print("Adding images for year '{0}'".format(year))
  yearroot = os.path.join(root, year)
  for img in os.listdir(yearroot):
    if img.endswith("jpg"):
      p.lpush("uploadq", uri.format(year, img))
      if not (count % 1000):
        p.execute()
        print("Queued %s images for upload" % count)
      count += 1
  p.execute()
