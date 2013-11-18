from cv2_detect import *

from Levenshtein import distance

from parse_xml import parse_xml

CV_SIGNALS = [slantyness, bubblyness, area]

MOOD = {'metadata': [1000.0, 20.0, 20.0, 20.0, 20.0, 0.5],
        'cv_signals': [50.0, 2.0, 1.0, 1.0, 1.0, 1.0]} 

SIGNAL_NAMES = ["identifier",
                "title",
                "author",
                "place_of_publishing", 
                "publisher", 
                "published_date",
                "slantyness",
                "bubblyness_avesize",
                "bubblyness_x",
                "bubblyness_y",
                "image_size",]

def breakdown_imagename(filename):
  id, vol, page, imgno, _ = filename.split("_",4)
  return id, vol, page, imgno

def gather_signals(filepath):
  print("Gathering signals for '{0}'".format(filepath))
  filename = filepath.split("/")[-1]
  id, vol, page, imgno = breakdown_imagename(filename.split("/")[-1])
  metadata = parse_xml(id)
  cv_signals = []
  for cv_measure in CV_SIGNALS:
    signal = cv_measure(filepath)
    if isinstance(signal, tuple):
      cv_signals.extend(signal)
    else:
      cv_signals.append(signal)
  return {'metadata': metadata,
          'identifier': (id, vol, page, imgno),
          'cv_signals': cv_signals}

def compare_metadata(prev, potential, mood):
  linked = zip(prev['metadata'], potential['metadata'])
  diffs = []
  for idx, items in enumerate(linked):
    old, new = items
    if idx == 5:
      # dates
      olddate, newdate = 0,0
      if len(old) == 4:
        olddate = int(old)
      if len(new) == 4:
        newdate = int(new)
      diffs.append(np.abs(newdate-olddate))
    else:
      try:
        if old != "" and new != "":
          diffs.append(distance(unicode(old), unicode(new)) / float(len(old) + len(new) + 1) )
        else:
          diffs.append(100000)
      except:
        diffs.append(distance((old), str(new)))
  weighted_diffs = map(lambda x: x[0]*x[1], zip(diffs, mood['metadata']))
  return weighted_diffs

def compare_cv(prev, potential, mood):
  figures = []
  deltas = []
  for a,b,c in zip(prev['cv_signals'], potential['cv_signals'], mood['cv_signals']):
    if a != None and b != None:
      deltas.append(np.abs(a-b) * c)
    else:
      deltas.append(1000000000)
  return deltas
    

def signal_combine(comparison):
  return sum(comparison)

def compare(previous_img_path, potential_img_path, mood=MOOD):
  prev = gather_signals(previous_img_path)
  potential = gather_signals(potential_img_path)
  md_comparison = compare_metadata(prev, potential, mood)
  cv_comparison = compare_cv(prev, potential, mood)
  return zip(SIGNAL_NAMES, md_comparison+cv_comparison)
