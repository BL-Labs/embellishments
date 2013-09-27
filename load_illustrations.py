from c19_paths import altopath_to_idvol
from redis import Redis
import time

r = Redis()

q = "total"
LIMIT = 10000
PAUSE = 1

illustrations = "illustration_list.txt"

jobs = 0
from collections import defaultdict
jobtally = defaultdict(lambda:0)
cur = 0.0
st = time.time()

with open(illustrations, "r") as ill_list:
  curid = ""
  curvol = ""
  pagelist = []
  for line in ill_list:
    path = line.strip()
    cur += 1
    id, vol, _ = altopath_to_idvol(path)
    jobtally[id[:4]] += 1
    if curid != ""  and (id != curid or vol != curvol):
      jobs += 1
      # r.lpush(q, "\t".join(pagelist))
      pagelist = []
      curid = id
      curvol = vol
    elif curid == "" or curvol == "":
      curid = id
      curvol = vol
      pagelist.append(path)
    else:
      pagelist.append(path)
    if not cur % LIMIT:
      print("{0} added. {1}/s".format(cur, (time.time()-st) / float(cur) ))
      #if r.llen(q) > LIMIT:
      #  print("Input Queue over {0}, pausing for {1}s".format(LIMIT, PAUSE))
      #  time.sleep(PAUSE)
  print("\n"+"="*30)
  print("Jobs added: {0}".format(jobs))
  for k in sorted(jobtally.keys()):
    print("ID division: {0} -> Pages to check {1}".format(k, jobtally[k]))
