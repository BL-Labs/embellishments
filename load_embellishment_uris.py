import os
from redis import Redis

r = Redis()

uri = "/static/e/{0}/{1}"
root = "/mnt/nas/embellishments"

for year in [x for x in os.listdir(root) if os.path.isdir(os.path.join(root, x))]:
  print("Adding {0} images...".format(year))
  yearroot = os.path.join(root, year)
  for img in os.listdir(yearroot):
    if img.endswith("jpg"):
      r.sadd("images", uri.format(year, img))
