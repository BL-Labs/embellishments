import os
import cv2
import cv2.cv as cv

nasmount = "/mnt/nas/"

JP2ZIPS = os.listdir(os.path.join(nasmount, "JP2"))

def id_to_path(id):
  return os.path.join(nasmount, "by_id", id[:4], id)

def altopath_to_id(winpath):
  return winpath[36:45]

def altopath_to_idvol(winpath):
  id = altopath_to_id(winpath)
  _, fn = winpath.rsplit("/", 1)
  if len(fn.split("_")) == 3:
    _, vol, page = fn.strip()[:-4].split("_")
    return id, vol, page
  else:
    _, page = fn.strip()[:-4].split("_")
    return id, "0", page

def altopath_to_imagename(winpath):
  id = altopath_to_id(winpath)
  _, fn = winpath.rsplit("/", 1)
  if len(fn.split("_")) == 3:
    _, vol, page = fn.strip()[:-4].split("_")
    return "JP2\\{0}_{1}_{2}.jp2".format(id, vol, page)
  else:
    _, page = fn.strip()[:-4].split("_")
    return "JP2\\{0}_{1}.jp2".format(id, page)

def altopath_to_jp2_zip(winpath):
  id = altopath_to_id(winpath)
  _, fn = winpath.rsplit("/", 1)
  vol = "0"
  if len(fn.split("_")) == 3:
    _, vol, _ = fn.split("_")
  vol = str(int(vol))
  return jp2_zip_path(id, vol)

def old_winpath_to_vmpath(winpath):
  # eg //192.168.15.153/C19Books/decrypted/000000037/ALTO/... to
  # /mnt/nas/by_id/0000/000000037/ALTO/...
  id = altopath_to_id(winpath)
  filename = winpath.split("/")[-1]
  return os.path.join(id_to_path(id), "ALTO", filename)

def jp2_zip_path(id, vol=0):
  zipstart = "{0}_{1}_".format(id, vol)
  match = [x for x in JP2ZIPS if x.startswith(zipstart)]
  if len(match) == 1:
    fullpath = os.path.join(nasmount, "JP2", match[0])
    if os.path.exists(fullpath):
      return fullpath
  return False

def parse_altopath(winpath):
  return altopath_to_jp2_zip(winpath), altopath_to_imagename(winpath)
